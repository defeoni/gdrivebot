#!/usr/bin/env python3.13
"""Test Google Generative AI API"""
import os
import sys

# Set test environment
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', '')

if not os.environ['GOOGLE_API_KEY']:
    print("❌ GOOGLE_API_KEY not set. Export it first:")
    print("   set GOOGLE_API_KEY=your_key_here")
    sys.exit(1)

try:
    import google.generativeai as genai
    print("✅ google-generativeai imported")
    
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    print("✅ Google API configured")
    
    # Test models
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for model_name in models_to_try:
        try:
            print(f"\n🔄 Testing model: {model_name}")
            model = genai.GenerativeModel(model_name)
            print(f"  ✅ Model {model_name} loaded")
            
            # Try a simple request
            response = model.generate_content(
                "Berikan jawaban singkat 'OK'",
                generation_config=genai.types.GenerationConfig(max_output_tokens=50, temperature=0.2)
            )
            
            if response.text:
                print(f"  ✅ Response from {model_name}: {response.text[:50]}")
                print(f"\n✅ SUCCESS: Model {model_name} works!")
                sys.exit(0)
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n❌ All models failed")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Install with: pip install google-generativeai")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
