#!/usr/bin/env python3
"""Simple test to check if Runware API is working."""

import asyncio
import os
import aiohttp
from pathlib import Path
from runware import Runware, IImageInference
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def download_image(url: str, save_path: Path) -> bool:
    """Download image from URL to local path."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Create directory if it doesn't exist
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write image data to file
                with open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                print(f"📁 Image downloaded to: {save_path}")
                return True
                
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return False


async def simple_test():
    """Generate a simple test image."""
    
    # Check for API key
    api_key = os.getenv("RUNWARE_API_KEY")
    if not api_key:
        print("❌ Please set RUNWARE_API_KEY in your environment")
        print("   Add this to your .env file:")
        print("   RUNWARE_API_KEY=your_api_key_here")
        return
    
    print("🐱 Testing Runware API with a simple image...")
    print("Generating: 'A cute cat playing with a soccer ball'")
    
    try:
        # Connect to Runware
        runware = Runware(api_key=api_key)
        await runware.connect()
        print("✅ Connected to Runware!")
        
        # Simple image request
        request = IImageInference(
            positivePrompt="A cute cat playing with a soccer ball",
            model="civitai:101055@128078",  # SDXL Base model
            numberResults=1,
            height=512,
            width=512,
        )
        
        # Generate image
        print("🎨 Generating image...")
        images = await runware.imageInference(requestImage=request)
        
        # Show result and download image
        for i, image in enumerate(images):
            print("🎉 Success! Image generated:")
            print(f"   URL: {image.imageURL}")
            
            # Define save path in web/www/images/public
            # Go up to project root, then to web/www/images/public
            project_root = Path(__file__).parent.parent.parent
            save_dir = project_root / "web" / "www" / "images" / "public"
            filename = f"cat_soccer_ball_{i+1}.jpg"
            save_path = save_dir / filename
            
            # Download the image
            print("📥 Downloading image...")
            success = await download_image(image.imageURL, save_path)
            
            if success:
                print("✅ Image saved successfully!")
                print(f"   Local path: {save_path}")
            else:
                print("❌ Failed to download image")
        
        await runware.disconnect()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(simple_test())
