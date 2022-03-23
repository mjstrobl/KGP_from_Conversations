import socketio

sio = socketio.Client()
sio.connect('http://localhost:3000')
print('my sid is', sio.sid)

@sio.on('client_message')
def on_message(msg):
    print('I received a message!')
    print(msg)

    text = msg['msg']

    msg['service'] = "rg"
    msg['message'] = "I'm good, how are you?"

    sio.emit('server_response', msg)




