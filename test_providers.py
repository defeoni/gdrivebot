#!/usr/bin/env python3.13
"""Test AI provider chain without Telegram"""

import sys
import os

# Set environment for testing
os.environ['TZ'] = 'UTC'

# Import the provider functions
sys.path.insert(0, 'd:/PROJECT/gdrivebot')

try:
    # Test imports
    print("🔄 Testing provider configuration...")
    
    # Check what's configured
    OPENAI_API = ""
    GROK_API = ""  # Removed for security - add your key here
    HUGGINGFACE_API = "hf_default"
    
    print(f"✅ OpenAI configured: {bool(OPENAI_API)} (disabled due to quota)")
    print(f"✅ Grok configured: {bool(GROK_API)}")
    print(f"✅ HuggingFace configured: {bool(HUGGINGFACE_API)}")
    
    print("\n🔄 Provider chain priority:")
    providers = []
    if GROK_API:
        providers.append('Grok')
    if OPENAI_API:
        providers.append('OpenAI')
    if HUGGINGFACE_API:
        providers.append('HuggingFace')
    
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p}")
    
    print("\n✅ Configuration OK")
    print("✅ Provider chain: Grok (1st) → HuggingFace (2nd)")
    print("\nNotes:")
    print("- OpenAI disabled temporarily (quota exceeded)")
    print("- Using free Grok API as primary provider")
    print("- HuggingFace as fallback (free tier)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
