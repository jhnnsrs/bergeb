#%%
from bergen.clients.default import Bergen
from bergen.models import Node
from bergen.wards.graphql.aiohttp import AIOHttpGraphQLWard
import asyncio
import time
from bergen.query import AsyncQuery

async def main():
        async with Bergen(
                host="p-tnagerl-lab1",
                port=8000,
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ", 
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
                name="karl",
                scopes= ["read"]# if we want to specifically only use pods on this innstance we would use that it in the selector
        ) as client:

                async with AIOHttpGraphQLWard(8080, "localhost", "http", client.token) as ward:
                

                        result = await AsyncQuery("""
                          query {
                                  hello
                         }     
                        """, str).run(ward=ward)

                        print(result)






if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
