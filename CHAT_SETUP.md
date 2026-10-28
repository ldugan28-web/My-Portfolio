# Public Chat Setup

The site and chat now run from one Python server. The chat uses server-sent events for live updates and keeps the latest 50 messages in memory. No Firebase account, keys, or third-party chat service are required.

## Run Locally

1. Stop any other server using port 8001.
2. From the project folder, run `python3 server.py`.
3. Open `http://localhost:8001/index.html`.
4. Open that address in another browser or device on the same network to test shared messages. On another device, replace `localhost` with the computer's LAN IP address and allow inbound connections on port 8001.

## Publish Online

1. Push the project folder to a GitHub repository.
2. In Render, create a new Web Service from that repository. The included `render.yaml` can configure the Python runtime, build command, and start command.
3. Deploy and open the `onrender.com` URL Render assigns to the service. Share that URL; the chat endpoint is hosted by the same service.

The server stores chat messages in memory, so the most recent 50 are shared while that server process is running. They are cleared when it restarts or redeploys. Guest display names are not verified, and there is no moderation or durable history; treat the room as public and do not share private information.