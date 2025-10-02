# Simple Runware Test

Quick test to check if Runware.ai API is working.

## Setup

1. **Get API Key**: Sign up at [runware.ai](https://runware.ai) and get your API key

2. **Set API Key**: Create a `.env` file in this directory:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your actual API key:
   ```
   RUNWARE_API_KEY=your_actual_api_key_here
   ```

3. **Run Test**:
   ```bash
   python simple_test.py
   ```

## What it does

- ✅ Checks if your API key is configured
- ✅ Connects to Runware API  
- ✅ Generates one test image: "A cute cat playing with a soccer ball"
- ✅ Shows you the image URL

That's it! 🐱⚽
