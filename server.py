
import asyncio
import json
import websockets



# rooms: mapping room_name -> set of websocket connections
rooms: dict[str, set] = {}
#owners
room_owners: dict[str, str] = {}
# map room_name -> password
room_passwords: dict[str, str] = {}
# map websocket -> room name
clients_room: dict = {}
# optional client display names
clients_name: dict = {}

streaming_rooms: dict[str, list] = {}

rooms_lock = asyncio.Lock()
_server = None
_loop = None
_stop_event = None
connected_clients: set = set()


def _get_ws_by_name(name):
	"""Return the websocket for a given client name, or None if not found."""
	if not name:
		return None
	for ws, nm in clients_name.items():
		if nm == name:
			return ws
	return None

async def send_json(ws, obj):
	try:
		await ws.send(json.dumps(obj))
	except Exception:
		pass

async def broadcast(room, obj, exclude_ws=None):
	"""Send `obj` (dict) to all clients in room. Optionally exclude one websocket."""
	if room not in rooms:
		return
	data = json.dumps(obj)
	coros = []
	for ws in set(rooms[room]):
		if ws == exclude_ws:
			continue
		coros.append(ws.send(data))
	if coros:
		await asyncio.gather(*coros, return_exceptions=True)

async def remove_client(ws):
	connected_clients.discard(ws)
	async with rooms_lock:
		room = clients_room.get(ws)
		if room:
			rooms[room].discard(ws)
			if len(rooms[room]) == 0:
					# remove empty room
					del rooms[room]
					# remove associated password if present
					if room in room_passwords:
						del room_passwords[room]
			else:
				# notify remaining clients about updated user count
				try:
					await broadcast(room, {"type": "user_count", "data": len(rooms[room])})
				except Exception:
					pass
			del clients_room[ws]
		if ws in clients_name:
			del clients_name[ws]

async def handler(websocket):
	connected_clients.add(websocket)
	addr = websocket.remote_address
	print(f"Client connected: {addr}")
	# default name
	clients_name[websocket] = f"user-{addr[1]}"
	try:
		# send protocol help
		await send_json(websocket, {"type": "welcome", "message": "Welcome. Send JSON actions: create/join/leave/message/list/set_name"})
		async for raw in websocket:
			try:
				msg = json.loads(raw)
			except Exception:
				await send_json(websocket, {"type": "error", "message": "invalid json"})
				continue

			action = msg.get("action")
			if action == "set_name":
				name = msg.get("name") or clients_name.get(websocket)
				clients_name[websocket] = name
				await send_json(websocket, {"type": "name_set", "name": name})

			elif action == "create":
				room = msg.get("room")
				password = msg.get("password")
				if not room:
					await send_json(websocket, {"type": "error", "message": "room required"})
					continue
				async with rooms_lock:
					if room in rooms:
						await send_json(websocket, {"type": "error", "message": "room already exists"})
						continue
					rooms[room] = set()
					# store the password (may be None)
					room_passwords[room] = password
					room_owners[room] = websocket
					rooms[room].add(websocket)
					clients_room[websocket] = room
				await broadcast(room, {"type": "user_count", "data": len(rooms[room])})
				await send_json(websocket, {"type": "created", "room": room})
			
			elif action == "join":
				room = msg.get("room")
				password = msg.get("password")
				if not room:
					await send_json(websocket, {"type": "error", "message": "room required"})
					continue
				async with rooms_lock:
					if room not in rooms:
						await send_json(websocket, {"type": "error", "message": "room does not exist"})
						continue
					# check password
					room_password = room_passwords.get(room)
					if room_password != "":
						if password == "":
							await send_json(websocket, {"type": "error", "message": "password required"})
							continue
						if room_password != password:
							await send_json(websocket, {"type": "error", "message": "incorrect password"})
							continue
					rooms[room].add(websocket)
					clients_room[websocket] = room
					await broadcast(room, {"type": "user_count", "data": len(rooms[room])})
					await send_json(websocket, {"type": "joined", "room": room})
					if room in streaming_rooms:
						url = streaming_rooms[room]["url"]
						is_paused = streaming_rooms[room]["is_paused"]
						await send_json(websocket, {"type": "streaming_data", "data": {"url":url, "is_paused":is_paused}})
					

				# notify room — include the joining user's name (not the websocket object)
				await broadcast(room, {"type": "notice", "message": f"{clients_name.get(websocket)} joined the room.", "joined_user": clients_name.get(websocket)})
				
				print(f"Client {addr} joined room {room}")

			elif action == "leave":
				room = clients_room.get(websocket)
				if not room:
					await send_json(websocket, {"type": "error", "message": "not in a room"})
					continue
				async with rooms_lock:
					# remove the room if the leaving client is the owner
					if room_owners.get(room) is websocket:
						rooms[room].discard(websocket)
						del clients_room[websocket]
						if room in rooms:
							room_users = []
							for user in rooms[room]:
								if user is not websocket:
									room_users.append(user)
							for user in room_users:
								rooms[room].discard(user)
								await send_json(user, {"type": "info", "message": "owner left the room, room deleted."})
								await send_json(user, {"type": "ui", "ui_action": "stop"})
								await send_json(user, {"type": "left", "room": room})
							if room in room_passwords:
								del room_passwords[room]
							if room in room_owners:
								del room_owners[room]
							if room in streaming_rooms:
								del streaming_rooms[room]
							del rooms[room]
							await send_json(websocket, {"type": "left", "room": room})
						continue
					rooms[room].discard(websocket)
					del clients_room[websocket]
					# compute updated count safely
					count = len(rooms.get(room, set()))
					if count > 0:
						# notify remaining clients
						await broadcast(room, {"type": "user_count", "data": count})
					else:
						# no clients left; remove empty room
						if room in rooms:
							del rooms[room]
							if room in room_passwords:
								del room_passwords[room]
					if room in streaming_rooms:
						loaded_users = streaming_rooms[room].get('loaded_count')
						streaming_rooms[room]['loaded_count'] = loaded_users - 1
				await broadcast(room, {"type": "notice", "message": f"{clients_name.get(websocket)} left the room."})
				await send_json(websocket, {"type": "left", "room": room})
				print(f"Client {addr} left room {room}")

			elif action == "message":
				text = msg.get("message")
				room = clients_room.get(websocket)
				if not room:
					await send_json(websocket, {"type": "error", "message": "join a room first"})
					continue
				sender = clients_name.get(websocket)
				await broadcast(room, {"type": "message", "room": room, "from": sender, "message": text}, exclude_ws=None)

			elif action == "loaded":
				room = msg.get("room")
				if not room:
					await send_json(websocket, {"type": "error", "message": "join a room first"})
					continue
				async with rooms_lock:
					if room not in rooms:
						await send_json(websocket, {"type": "error", "message": "room does not exist"})
						continue
					if room not in streaming_rooms:
						await send_json(websocket, {"type": "error", "message": "No url is being played"})
						continue
					loaded_users = streaming_rooms[room].get('loaded_count')
					streaming_rooms[room]['loaded_count'] = loaded_users + 1

			elif action == "current_time":
				room = msg.get("room")
				target_name = msg.get("joined_user")
				time = msg.get("time")
				sent_at = msg.get("sent_at")
				if room in streaming_rooms:
					# resolve the target websocket by name
					target_ws = None
					if isinstance(target_name, str):
						target_ws = _get_ws_by_name(target_name)
					# if we found a websocket, send the UI change
					if target_ws is not None:
						await send_json(target_ws, {"type": "ui", "ui_action": "change_time", "params":{"time":time, "sent_at":sent_at}})

			elif action == "ui":
				# UI actions from a client should be forwarded to other clients in the same room
				ui_action = msg.get("ui_action")
				params = msg.get("params", {})
				room = clients_room.get(websocket)
				if ui_action == "open_url":
					try:
						streaming_rooms[room]['url'] = params["url"]
						streaming_rooms[room]['loaded_count'] = 0
					except:
						# store only JSON-serializable info about the stream; avoid storing websocket objects
						streaming_rooms[room] = dict(params) if isinstance(params, dict) else params
						streaming_rooms[room]["owner"] = room_owners.get(room)
						streaming_rooms[room]["is_paused"] = True
						streaming_rooms[room]["loaded_count"] = 0
						await send_json(room_owners.get(room), {"type": "is_owner", "value": True})
				if ui_action == "pause":
					if room in streaming_rooms:
						loaded_users = streaming_rooms[room].get('loaded_count')
						if len(rooms[room]) != loaded_users:
							await send_json(websocket, {"type": "error", "message": "You can't play the video unless everybody is loaded."})
							continue
						is_paused = bool(streaming_rooms[room].get('is_paused'))
						streaming_rooms[room]['is_paused'] = not is_paused

				if ui_action == "stop":
					if room in streaming_rooms:
						del streaming_rooms[room]
				if not room:
					await send_json(websocket, {"type": "error", "message": "join a room first"})
					continue
				# broadcast to other clients in the room only
				# include current is_paused state when available so clients open paused/playing consistently
				payload_params = dict(params) if isinstance(params, dict) else {}
				if room in streaming_rooms and isinstance(streaming_rooms[room], list) and len(streaming_rooms[room]) > 1:
					payload_params["is_paused"] = streaming_rooms[room].get("is_paused")
				await broadcast(room, {"type": "ui", "ui_action": ui_action, "params": payload_params, "from": clients_name.get(websocket)}, exclude_ws=websocket)

			elif action == "list":
				# return list of rooms and counts
				async with rooms_lock:
					info = {r: len(rooms[r]) for r in rooms}
				await send_json(websocket, {"type": "rooms", "rooms": info})

			else:
				await send_json(websocket, {"type": "error", "message": "unknown action"})

	except websockets.exceptions.ConnectionClosedOK:
		pass
	except Exception as e:
		print("WebSocket handler error:", e)
	finally:
		# cleanup
		print(f"Client disconnected: {addr}")


async def _close_all_clients():
	if not connected_clients:
		return
	clients = list(connected_clients)
	for ws in clients:
		try:
			await ws.close()
		except Exception:
			pass
	await asyncio.sleep(0.05)


async def _shutdown_server():
	global _server, _loop, _stop_event
	if _server is not None:
		try:
			await _close_all_clients()
			_server.close()
			await _server.wait_closed()
		except Exception as exc:
			print(f"Server shutdown error: {exc}")
		finally:
			_server = None
			print("Server stopped.")

	if _stop_event is not None:
		_stop_event.set()
		_stop_event = None

	_loop = None


async def _serve_forever():
	global _server, _loop, _stop_event
	_loop = asyncio.get_running_loop()
	_stop_event = asyncio.Event()
	print(f"Starting WebSocket server on {HOST}:{PORT}")
	try:
		_server = await websockets.serve(handler, HOST, PORT)
		await _stop_event.wait()
	finally:
		await _shutdown_server()


def stop():
	global _server, _loop, _stop_event
	if _server is None and _stop_event is None:
		return

	loop = _loop
	if loop is None:
		try:
			loop = asyncio.get_running_loop()
		except RuntimeError:
			loop = None

	if loop is not None and loop.is_running():
		if _stop_event is not None:
			loop.call_soon_threadsafe(_stop_event.set)
		if loop is not asyncio.get_running_loop():
			try:
				future = asyncio.run_coroutine_threadsafe(_shutdown_server(), loop)
				future.result(timeout=5)
			except Exception as exc:
				print(f"Server shutdown error: {exc}")
		return

	try:
		asyncio.run(_shutdown_server())
	except RuntimeError:
		pass


def start():
	global HOST, PORT
	HOST = input("Enter a host IP (leave blank to use localhost):")
	if HOST == "":
		HOST = '127.0.0.1'
	PORT = 8765
	try:
		asyncio.run(_serve_forever())
	except KeyboardInterrupt:
		print("Server stopped by user")
		stop()


def main():
	start()


if __name__ == "__main__":
	main()



