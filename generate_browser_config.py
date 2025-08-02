#!/usr/bin/env python3
"""
Generate browser extension config.js from environment variables.
"""
import os
from pathlib import Path

def generate_config():
    # Get the service target from environment variable
    service_target = os.getenv('CLAUDE_SERVICE_TARGET', 'http://127.0.0.1:8000/chat')
    
    # Config content
    config_content = f"""// Configuration for the browser extension
// This file is generated from environment variables
const CONFIG = {{
    SERVICE_URL: '{service_target}'
}};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = CONFIG;
}}"""
    
    # Write to browser extension directory
    config_path = Path(__file__).parent / 'browser-extension' / 'config.js'
    config_path.write_text(config_content)
    
    print(f"Generated config.js with SERVICE_URL: {service_target}")

if __name__ == "__main__":
    generate_config()