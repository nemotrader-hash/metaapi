#!/usr/bin/env python3
"""
MetaApi Multi-Instance Launcher
==============================

Launch multiple MetaApi instances with different configurations.
Requires user-provided MT5 path for each instance, supports port management, and process monitoring.

Usage:
    python launcher.py --help
    python launcher.py start --instance demo1 --mt5-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe" --port 8087
    python launcher.py start --instance live1 --mt5-path "/path/to/mt5/terminal64.exe" --port 8088 --config instances/live1_config.json
    python launcher.py list
    python launcher.py stop --instance demo1
    python launcher.py stop --all
"""

import argparse
import json
import os
import sys
import time
import subprocess
import signal
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from config.config_manager import ConfigManager, AppConfig
from core.exceptions import ConfigurationError


@dataclass
class InstanceConfig:
    """Configuration for a MetaApi instance."""
    name: str
    port: int
    config_file: str
    mt5_path: str
    log_file: str
    pid_file: str
    status: str = "stopped"
    started_at: Optional[str] = None
    process_id: Optional[int] = None


class InstanceManager:
    """Manages multiple MetaApi instances."""
    
    def __init__(self, instances_dir: str = "instances"):
        self.instances_dir = Path(instances_dir)
        self.instances_dir.mkdir(exist_ok=True)
        self.registry_file = self.instances_dir / "registry.json"
        self.instances: Dict[str, InstanceConfig] = self._load_registry()
    
    def _load_registry(self) -> Dict[str, InstanceConfig]:
        """Load instance registry from file."""
        if not self.registry_file.exists():
            return {}
        
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
            
            instances = {}
            for name, config_data in data.items():
                instances[name] = InstanceConfig(**config_data)
            
            return instances
        except Exception as e:
            print(f"⚠️  Warning: Could not load registry: {e}")
            return {}
    
    def _save_registry(self):
        """Save instance registry to file."""
        try:
            data = {}
            for name, instance in self.instances.items():
                data[name] = asdict(instance)
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving registry: {e}")
    
    def _get_next_available_port(self, start_port: int = 8087) -> int:
        """Find the next available port."""
        used_ports = {instance.port for instance in self.instances.values()}
        
        port = start_port
        while port in used_ports or self._is_port_in_use(port):
            port += 1
            if port > 9999:  # Reasonable upper limit
                raise RuntimeError("No available ports found")
        
        return port
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    

    
    def _create_instance_config(self, instance_name: str, mt5_path: str, base_config: str = None) -> str:
        """Create instance-specific configuration file."""
        config_file = self.instances_dir / f"{instance_name}_config.json"
        
        if base_config and Path(base_config).exists():
            # Copy from base config
            config_manager = ConfigManager(base_config)
            config = config_manager.get_config()
        else:
            # Create default config
            config = AppConfig(
                secret_key=f"MetaApi_{instance_name}_key",
                telegram_bot_token="YOUR_TELEGRAM_BOT_TOKEN",
                telegram_chat_id=0,
                debug=False,
                host="0.0.0.0",
                port=8087,  # Will be updated
                mt5_path="",  # Will be updated
                rate_limit_per_minute=300,
                request_timeout=30,
                log_level="INFO"
            )
        
        # Validate and set MT5 path
        if not Path(mt5_path).exists():
            raise ValueError(f"MT5 path does not exist: {mt5_path}")
        config.mt5_path = mt5_path
        
        # Save config
        config_dict = {
            "secret_key": config.secret_key,
            "telegram_bot_token": config.telegram_bot_token,
            "telegram_chat_id": config.telegram_chat_id,
            "debug": config.debug,
            "host": config.host,
            "port": config.port,
            "mt5_path": config.mt5_path,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "request_timeout": config.request_timeout,
            "log_level": config.log_level,
            "features": {
                "rate_limiting": True,
                "request_logging": True,
                "metrics_collection": True,
                "input_validation": True,
                "middleware": True
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        return str(config_file)
    
    def create_instance(self, name: str, mt5_path: str, port: Optional[int] = None, config_file: Optional[str] = None) -> InstanceConfig:
        """Create a new MetaApi instance."""
        if name in self.instances:
            raise ValueError(f"Instance '{name}' already exists")
        
        # Auto-assign port if not provided
        if port is None:
            port = self._get_next_available_port()
        elif port in {instance.port for instance in self.instances.values()}:
            raise ValueError(f"Port {port} is already in use by another instance")
        
        # Create instance-specific config
        if config_file is None:
            config_file = self._create_instance_config(name, mt5_path)
        else:
            config_file = self._create_instance_config(name, mt5_path, config_file)
        
        # Update port in config
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        config_data['port'] = port
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Create instance
        instance = InstanceConfig(
            name=name,
            port=port,
            config_file=config_file,
            mt5_path=mt5_path,
            log_file=str(self.instances_dir / f"{name}.log"),
            pid_file=str(self.instances_dir / f"{name}.pid")
        )
        
        self.instances[name] = instance
        self._save_registry()
        
        return instance
    
    def start_instance(self, name: str) -> bool:
        """Start a MetaApi instance."""
        if name not in self.instances:
            raise ValueError(f"Instance '{name}' does not exist")
        
        instance = self.instances[name]
        
        # Check if already running
        if self._is_instance_running(instance):
            print(f"⚠️  Instance '{name}' is already running")
            return False
        
        try:
            # Start the instance
            cmd = [
                sys.executable, "app.py",
                "--config", instance.config_file,
                "--port", str(instance.port)
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env['METAAPI_CONFIG_FILE'] = instance.config_file
            env['METAAPI_INSTANCE_NAME'] = instance.name
            
            # Start process
            with open(instance.log_file, 'w') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=os.getcwd()
                )
            
            # Save PID
            with open(instance.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Update instance status
            instance.status = "running"
            instance.started_at = datetime.now().isoformat()
            instance.process_id = process.pid
            
            self._save_registry()
            
            print(f"🚀 Started instance '{name}' on port {instance.port} (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start instance '{name}': {e}")
            return False
    
    def stop_instance(self, name: str) -> bool:
        """Stop a MetaApi instance."""
        if name not in self.instances:
            raise ValueError(f"Instance '{name}' does not exist")
        
        instance = self.instances[name]
        
        try:
            # Read PID
            if not Path(instance.pid_file).exists():
                print(f"⚠️  No PID file found for instance '{name}'")
                return False
            
            with open(instance.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Terminate process
            try:
                process = psutil.Process(pid)
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if necessary
                    process.kill()
                    process.wait()
                
                print(f"🛑 Stopped instance '{name}' (PID: {pid})")
                
            except psutil.NoSuchProcess:
                print(f"⚠️  Process {pid} for instance '{name}' was not running")
            
            # Cleanup
            Path(instance.pid_file).unlink(missing_ok=True)
            
            # Update status
            instance.status = "stopped"
            instance.started_at = None
            instance.process_id = None
            
            self._save_registry()
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop instance '{name}': {e}")
            return False
    
    def _is_instance_running(self, instance: InstanceConfig) -> bool:
        """Check if an instance is currently running."""
        if not Path(instance.pid_file).exists():
            return False
        
        try:
            with open(instance.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    def list_instances(self) -> List[InstanceConfig]:
        """List all instances with their status."""
        # Update running status
        for instance in self.instances.values():
            if self._is_instance_running(instance):
                instance.status = "running"
            else:
                instance.status = "stopped"
                instance.started_at = None
                instance.process_id = None
        
        self._save_registry()
        return list(self.instances.values())
    
    def stop_all_instances(self) -> int:
        """Stop all running instances."""
        stopped_count = 0
        for name in list(self.instances.keys()):
            if self.stop_instance(name):
                stopped_count += 1
        return stopped_count
    
    def remove_instance(self, name: str) -> bool:
        """Remove an instance."""
        if name not in self.instances:
            raise ValueError(f"Instance '{name}' does not exist")
        
        instance = self.instances[name]
        
        # Stop if running
        if self._is_instance_running(instance):
            self.stop_instance(name)
        
        # Remove files
        for file_path in [instance.config_file, instance.log_file, instance.pid_file]:
            Path(file_path).unlink(missing_ok=True)
        
        # Remove from registry
        del self.instances[name]
        self._save_registry()
        
        print(f"🗑️  Removed instance '{name}'")
        return True


def main():
    """Main launcher entry point."""
    parser = argparse.ArgumentParser(description="MetaApi Multi-Instance Launcher")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start an instance")
    start_parser.add_argument("--instance", "-i", required=True, help="Instance name")
    start_parser.add_argument("--mt5-path", "-m", required=True, help="Path to MetaTrader 5 terminal executable (e.g., 'C:\\Program Files\\MetaTrader 5\\terminal64.exe')")
    start_parser.add_argument("--port", "-p", type=int, help="Port number (auto-assigned if not specified)")
    start_parser.add_argument("--config", "-c", help="Base config file to copy from")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop an instance")
    stop_parser.add_argument("--instance", "-i", help="Instance name")
    stop_parser.add_argument("--all", action="store_true", help="Stop all instances")
    
    # List command
    subparsers.add_parser("list", help="List all instances")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an instance")
    remove_parser.add_argument("--instance", "-i", required=True, help="Instance name")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show instance status")
    status_parser.add_argument("--instance", "-i", help="Instance name (shows all if not specified)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = InstanceManager()
    
    try:
        if args.command == "start":
            # Create or start instance
            if args.instance not in manager.instances:
                print(f"📦 Creating new instance '{args.instance}'...")
                manager.create_instance(args.instance, args.mt5_path, args.port, args.config)
            
            manager.start_instance(args.instance)
            
        elif args.command == "stop":
            if args.all:
                count = manager.stop_all_instances()
                print(f"🛑 Stopped {count} instances")
            elif args.instance:
                manager.stop_instance(args.instance)
            else:
                print("❌ Please specify --instance or --all")
                
        elif args.command == "list" or args.command == "status":
            instances = manager.list_instances()
            if not instances:
                print("📭 No instances found")
                return
            
            print(f"{'Instance':<15} {'Status':<10} {'Port':<6} {'PID':<8} {'Started':<20} {'Config'}")
            print("-" * 80)
            
            for instance in instances:
                started = instance.started_at[:19] if instance.started_at else "-"
                pid = str(instance.process_id) if instance.process_id else "-"
                status_icon = "🟢" if instance.status == "running" else "🔴"
                
                print(f"{instance.name:<15} {status_icon}{instance.status:<9} {instance.port:<6} {pid:<8} {started:<20} {Path(instance.config_file).name}")
                
        elif args.command == "remove":
            manager.remove_instance(args.instance)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
