import fastapi
from fastapi.responses import HTMLResponse
import manager   
## this is just barebones, WIP.


app = fastapi.FastAPI()
serverManager = manager.MinecraftServerManager()


htmltest ="""
  <!DOCTYPE html>
  <html>
  <head>
      <title>Minecraft server manager</title>
  </head>
  <body>
      <h1>Welcome!</h1>
      <form action="/startServer/" method="POST">
      <button type="submit">start your server:</button>
      </form>
      
      <form action="/command" method="post">
      <label for="cmd">Commands:</label><br>
      <input type="text" id="cmd" name="cmd" placeholder="execute a minecraft command here, or dont, i dont care."><br><br>
      <input type="submit" value="Submit">
      </form>
  </body>
  </html>
"""


@app.get("/")
async def root():
    return HTMLResponse(htmltest)

@app.post("/command/{cmd}")
async def run_command(cmd, id):
    server = serverManager

@app.post("/startServer/")
async def startServer(ram : str = "placeholder", jar : str = 'placeholder', java : str = 'placeholder'):
    server = serverManager.create_server(ram, jar, java)
    return("server started")
    
    
    