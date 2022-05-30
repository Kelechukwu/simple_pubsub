
from collections import defaultdict
import types
import socket
import selectors
import sys

from enums import Command

sel = selectors.DefaultSelector()

unconsumed_events = defaultdict(dict)
subscribers = defaultdict(list)


def subscribe(event, sub):
    subscribers[event].append(sub)
    print(f"{sub} SUBSCRIBED to {event}")
    res = f"SUBSCRIBED to {event}"
    return res

def unsubscribe(event, sub):
    subscribers[event].remove(sub)
    res = f"UNSUBSCRIBED from {event}"
    print(f"{sub} UNSUBSCRIBED from {event}")

    return res

def publish(event, data):
    # send to all subs,
    # if subs are not reachable add event to missed events
    # { 
    #   sub1: {
    #           event1: [data1],
    #           event2: [data2, data3],
    #         } 
    # }
    # unconsumed_events[sub][event].append(data)
    pass


COMMAND_HANDLERS = {
    Command.UNSUB: unsubscribe,
    Command.PUB: publish,
    Command.SUB: subscribe,
}


def process_command(text: str, client_addr: str):
    command_arr = text.split(" ")
    try:
        command = Command(command_arr[0].upper())
        fn = COMMAND_HANDLERS[command]

        return fn(command_arr[1], client_addr)
    except ValueError:
        return f"UNKNOWN command: {command_arr[0]}"

def get_missed_events(event, sub):
    idx = []
    for data in unconsumed_events[sub][event]:
        # send_to_sub(data, sub)
        # if sucessfully consumed store idx to delete later.
        pass


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")

    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            # print(f"Echoing {data.outb!r} to {data.addr}")
            response = process_command(data.outb.decode(), data.addr)
            # sent = sock.send(data.outb)  # Should be ready to write
            sent = sock.send(response.encode())
            data.outb = data.outb[sent:]


def main():
    HOST = "127.0.0.1"
    PORT = 65432

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()

    print(f"Listening on {(HOST, PORT)}")

    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None: # no data sent, then it must be a connection request
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)

    except KeyboardInterrupt:
        print("Caught a keyboard interrupt. Exiting...")
    finally:
        sel.close()


if __name__ == "__main__":
    main()
