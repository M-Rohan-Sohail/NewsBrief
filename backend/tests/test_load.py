import asyncio
import httpx
import time
import os

# We will test the / get endpoint for load, 
# because /briefing/today requires a valid auth token which we might not have in the test environment
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

async def fetch_home(client, i):
    try:
        response = await client.get(f"{API_URL}/")
        return response.status_code
    except Exception as e:
        return str(e)

async def run_load_test(concurrent_users=100):
    print(f"Starting load test with {concurrent_users} concurrent requests to {API_URL}/ ...")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(concurrent_users):
            tasks.append(fetch_home(client, i))
            
        results = await asyncio.gather(*tasks)
        
    end_time = time.time()
    
    success_count = sum(1 for r in results if r == 200)
    error_count = len(results) - success_count
    
    print(f"Load test completed in {end_time - start_time:.2f} seconds.")
    print(f"Successful requests: {success_count}/{concurrent_users}")
    print(f"Failed requests: {error_count}/{concurrent_users}")
    
    if success_count == concurrent_users:
        print("✅ Load test passed!")
    else:
        print("❌ Load test failed some requests!")
        
    assert success_count > 0, "All requests failed! Is the server running?"

if __name__ == "__main__":
    asyncio.run(run_load_test(100))
