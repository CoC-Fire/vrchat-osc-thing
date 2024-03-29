import winreg
from pythonosc import *
import winsdk.windows.media.control
from pythonosc import udp_client
import psutil
import GPUtil
import asyncio
import concurrent
import concurrent.futures

ip = input("Enter your quest device's local IP address: ")
ip = ip.strip()
ip = ip.replace(" ", "")

executor = concurrent.futures.ThreadPoolExecutor(max_workers = 4)
client = udp_client.SimpleUDPClient(ip, 9000)

def refresh_client():
    global client
    del client
    ip = input("Enter your quest device's local IP address: ")
    ip = ip.strip()
    ip = ip.replace(" ", "")
    client = udp_client.SimpleUDPClient(ip, 9000)

def format_bytes(bytes_size):
    gb_size = bytes_size / (1024 ** 3)
    formatted = "{:.2f}".format(gb_size)
    return formatted

async def get_media_manager():
    manager = winsdk.windows.media.control.GlobalSystemMediaTransportControlsSessionManager.request_async()
    await asyncio.sleep(2)
    manager = manager.get_results()
    return manager

newline_char = " "

def send_chatbox_message(text: str):
    text = text.strip()
    text = text.replace("\n", newline_char)
    client.send_message("/chatbox/input", [text, True, False])

async def get_network_usage():
    net_start = psutil.net_io_counters()
    await asyncio.sleep(1)
    net_end = psutil.net_io_counters()

    start = net_start.bytes_sent + net_start.bytes_recv
    end = net_end.bytes_sent + net_end.bytes_recv

    net_total = end - start
    speed = (net_total * 8) / 1e6
    formatted = "{:.2f}".format(speed)

    return formatted

async def get_media_message():
    try:
        manager = winsdk.windows.media.control.GlobalSystemMediaTransportControlsSessionManager.request_async()
        await asyncio.sleep(2)
        manager = manager.get_results()

        session = manager.get_current_session()
        timeline = session.get_timeline_properties()

        results = session.try_get_media_properties_async()
        await asyncio.sleep(2)
        results = results.get_results()

        title = results.title
        artist = results.artist

        current_time = timeline.position.total_seconds()
        current_time = int(current_time)
        total_time = timeline.end_time.total_seconds()
        total_time = int(total_time)

        if float(total_time / 60) >= 1.0:
            total_time_minutes = int(total_time / 60)
        else:
            total_time_minutes = 0

        total_seconds = total_time_minutes * 60
        total_time_seconds = total_time - total_seconds

        if len(str(total_time_seconds)) < 2:
            total_time_seconds = "0" + str(total_time_seconds)
        if float(current_time / 60) >= 1.0:
            current_time_minutes = int(current_time / 60)
        else:
            current_time_minutes = 0

        current_seconds = current_time_minutes * 60
        current_time_seconds = current_time - current_seconds

        if len(str(current_time_seconds)) < 2:
            current_time_seconds = "0" + str(current_time_seconds)

        thing = f"[{current_time_minutes}:{current_time_seconds}/{total_time_minutes}:{total_time_seconds}]"
        message = f"""
Free Music & No Ads
https://ezmusic.net/

{artist} - {title}
{thing}
"""
    except:
        await asyncio.sleep(2)
        message = f"""
Free Music & No Ads
https://ezmusic.net/

Nothing is playing
"""

    return message

async def get_stats_message():
    ram = psutil.virtual_memory()
    try:
        gpu = GPUtil.getGPUs()[0]
        gpuname = gpu.name
        gpu = float(gpu.load * 100)
        gpu = str(gpu)
        gpu = gpu.split(".")[0]
    except Exception as e:
        gpuname = "GPU"
        gpu = None

    cpu = psutil.cpu_percent(interval=1, percpu=False)
    cpu = str(cpu)
    parts = cpu.split(".")

    if len(parts[1]) > 2:
        cpu = parts[0] + "." + parts[1][2:]
    elif len(parts[1]) == 1:
        cpu = parts[0] + ".0" + parts[1]

    speed = await get_network_usage()
    message = f"""
{get_processor_brand()}: {cpu}%
{gpuname}: {gpu}%
RAM Usage: {format_bytes(ram.used)}/{format_bytes(ram.total)} GB
Network Usage: {speed} Mbps
"""

    return message

def get_processor_brand():
    try:
        registry_key = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_key) as key:
            processor_brand, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            return processor_brand
    except Exception as e:
        return None

def update_client_listener():
    while True:
        input()
        refresh_client()

async def update_client_listener_async():
    await asyncio.get_event_loop().run_in_executor(executor, lambda: update_client_listener())

async def main():
    while True:
        message = await get_stats_message()
        send_chatbox_message(message)
        message = await get_media_message()
        send_chatbox_message(message)
        await asyncio.sleep(2)

loop = asyncio.new_event_loop()
loop.create_task(main())
loop.create_task(update_client_listener_async())
loop.run_forever()