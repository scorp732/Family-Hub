#!/usr/bin/env python3
import os
import sys
import logging
import subprocess
import argparse
import signal
import socket
import time
import atexit
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('family_hub')

# Global variables
streamlit_process = None
app_port = 13795

def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments object
    """
    parser = argparse.ArgumentParser(description='Run Family Hub application')
    parser.add_argument('--port', type=int, default=13795,
                        help='Port to run the application on (default: 13795)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with additional logging')
    parser.add_argument('--no-auto-kill', action='store_true',
                        help='Do not automatically kill processes using the specified port')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host address to bind to (default: 0.0.0.0)')
    return parser.parse_args()

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """
    Kill any process using the specified port
    
    This function is specifically designed to kill processes using the Family Hub port,
    as this port is reserved exclusively for this application.
    """
    try:
        # Use a more direct approach with system commands
        import subprocess
        import platform
        
        # Different commands based on OS
        system = platform.system()
        
        if system == "Linux":
            # For Linux
            cmd = f"fuser -k {port}/tcp"
            subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
            logger.info(f"Killed any process using port {port} on Linux")
            return True
        elif system == "Darwin":  # macOS
            # For macOS
            cmd = f"lsof -i :{port} -t | xargs kill -9"
            subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
            logger.info(f"Killed any process using port {port} on macOS")
            return True
        elif system == "Windows":
            # For Windows
            cmd = f"for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{port}') do taskkill /F /PID %a"
            subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
            logger.info(f"Killed any process using port {port} on Windows")
            return True
        else:
            logger.warning(f"Unsupported OS: {system}")
            
        # Fallback to psutil if the OS-specific approach fails
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    connections = proc.connections()
                    for conn in connections:
                        if hasattr(conn, 'laddr') and hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                            logger.info(f"Killing process {proc.pid} ({proc.name()}) using port {port}")
                            proc.terminate()
                            proc.wait(timeout=3)
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                    continue
        except Exception as e:
            logger.warning(f"Psutil approach failed: {e}")
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {e}")
    
    # Even if we couldn't confirm the kill, we'll proceed anyway
    # since the port might actually be free or the process might have been killed
    return True

def cleanup():
    """
    Clean up resources before exiting
    
    This ensures that the port is properly released when the application exits,
    preventing port conflicts on subsequent runs.
    """
    global streamlit_process, app_port
    
    logger.info("Cleaning up resources...")
    
    # Terminate Streamlit process if it's running
    if streamlit_process and streamlit_process.poll() is None:
        logger.info("Terminating Streamlit process...")
        try:
            streamlit_process.terminate()
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Streamlit process did not terminate gracefully, forcing...")
            streamlit_process.kill()
    
    # Make sure the port is released
    if is_port_in_use(app_port):
        logger.info(f"Ensuring port {app_port} is released...")
        kill_process_on_port(app_port)
    
    logger.info("Cleanup complete")

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

def main():
    """Main entry point for the application"""
    global streamlit_process, app_port
    
    args = parse_arguments()
    app_port = args.port
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to run on exit
    atexit.register(cleanup)
    
    # Always free the port - this is our dedicated port
    host = args.host
    
    if is_port_in_use(app_port):
        logger.info(f"Port {app_port} is in use. Freeing it for Family Hub...")
        kill_process_on_port(app_port)
        
        # Wait a moment for the port to be released
        time.sleep(1)
        
        # Double-check the port is now available
        if is_port_in_use(app_port):
            logger.warning(f"Port {app_port} is still in use after attempting to free it.")
            if args.no_auto_kill:
                logger.error(f"Port {app_port} is in use and --no-auto-kill was specified. Please free the port manually.")
                sys.exit(1)
    
    # Set environment variables
    os.environ['STREAMLIT_SERVER_PORT'] = str(app_port)
    
    if args.debug:
        os.environ['STREAMLIT_LOGGER_LEVEL'] = 'debug'
        os.environ['FAMILY_HUB_DEBUG'] = 'true'
        logging.getLogger('family_hub').setLevel(logging.DEBUG)
    
    logger.info(f"Starting Family Hub on port {app_port} (host: {host})")
    
    # Run the Streamlit application
    try:
        streamlit_cmd = [
            "streamlit", "run",
            "main.py",
            "--server.port", str(app_port),
            "--server.address", host,
            "--browser.serverAddress", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        logger.debug(f"Running command: {' '.join(streamlit_cmd)}")
        streamlit_process = subprocess.Popen(streamlit_cmd)
        
        # Print a helpful message
        print(f"\n{'='*60}")
        print(f"Family Hub is running at http://localhost:{app_port}")
        print(f"Press Ctrl+C to stop the application")
        print(f"{'='*60}\n")
        
        # Wait for the process to complete
        streamlit_process.wait()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    finally:
        cleanup()
    
    logger.info("Application stopped")

if __name__ == "__main__":
    main()