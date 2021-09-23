# -*- coding: utf-8 -*-

"""Console script for xled."""

from __future__ import absolute_import
from PIL import Image
from PIL import GifImagePlugin

import logging
import time
import socket
import csv

import click
import click_log

import xled.auth
import xled.control
import xled.discover
import xled.exceptions
import xled.security

log = logging.getLogger(__name__)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

log.addHandler(ch)


def common_preamble(name=None, host_address=None):
    if name:
        click.echo("Looking for a device with name: {}...".format(name))
    elif host_address:
        click.echo("Looking for device with address: {}...".format(host_address))
    else:
        click.echo("Looking for any device...")
    hw_address, device_name, ip_address = xled.discover.discover(
        find_id=name, destination_host=host_address
    )
    if name:
        click.echo("Working on requested device.")
    else:
        click.echo("Working on device: {}".format(device_name))
    log.debug("HW address = %s", hw_address)
    log.debug("IP address = %s", ip_address)

    return xled.control.HighControlInterface(ip_address, hw_address)


def validate_time(ctx, param, value):
    try:
        struct_time = time.strptime(value, "%H:%M")
        return (struct_time.tm_hour, struct_time.tm_min)
    except ValueError:
        raise click.BadParameter("Time needs to be in format HH:MM.")


@click.group()
@click.version_option()
@click.pass_context
@click.option(
    "--name",
    metavar="DEVICE_NAME",
    help="Name of the device to operate on. Mutually exclusive with --hostname.",
)

@click.option(
    "--hostname",
    metavar="ADDRESS",
    help="Address of the device to operate on. Mutually exclusive with --name.",
)
@click_log.simple_verbosity_option(
    log,
    "--verbosity-cli",
    help="Sets verbosity of main CLI. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
@click_log.simple_verbosity_option(
    xled.discover.log,
    "--verbosity-discover",
    help="Sets verbosity of discover module. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
@click_log.simple_verbosity_option(
    xled.control.log,
    "--verbosity-control",
    help="Sets verbosity of control module. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)
@click_log.simple_verbosity_option(
    xled.auth.log,
    "--verbosity-auth",
    help="Sets verbosity of auth module. Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
)

def main(ctx, name, hostname):
    if name and hostname:
        raise click.BadParameter("Either name or hostname can be set not both.")
    ctx.obj = {"name": name, "hostname": hostname}


@main.command(name="get-mode", help="Gets current device mode.")
@click.pass_context
def get_mode(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    mode = control_interface.get_mode()
    click.echo("Device in mode {}.".format(mode["mode"]))


@main.command(name="on", help="Turns device on and starts last used movie.")
@click.pass_context
def turn_on(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Turning on...")
    control_interface.turn_on()
    click.echo("Turned on.")


@main.command(name="off", help="Turns device off.")
@click.pass_context
def turn_off(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Turning off...")
    control_interface.turn_off()
    click.echo("Turned off.")

@main.command(name="realtime", help="Turns realtime on.")
@click.option(
    '-g',
    '--gif',
    metavar="GIF_PATH",
    help="gif file to feed --gif.",
)
@click.pass_context
def realtime(ctx, gif):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Get device info...")
    response = control_interface.get_device_info()
    number_of_led = response["number_of_led"]
    led_profile = response["led_profile"]
    bytes_per_led = len(led_profile);
    max_frame = (bytes_per_led*number_of_led)
    click.echo("LED profile: {}".format(led_profile))
    click.echo("Format: {}".format(number_of_led))
    click.echo("Bytes per LED: {}".format(bytes_per_led))
    click.echo("Max Frame Size: {}".format(max_frame))
    click.echo("Max Packet Size: {}".format(max_frame+10))
    log.debug("Loading xled.map");
    map = []


    #Create a database from a csv. each cell has the led number.
    #I have a 15x15 grid for a 250 string, some ommited
    with open("./xled.map") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            map.append(row)

    map_width = len(map[0]);
    map_height = len(map);
    click.echo("Map Width: {}".format(map_width))
    click.echo("Map Height: {}".format(map_height))

    image = Image.open(gif)

    log.debug("Turning realtime on...")
    control_interface.realtime()
    click.echo("Realtime turned on. Send packets to {}:7777".format(control_interface.host))
    click.echo("Authentication Token: {} / {}".format(
        control_interface._session.access_token,
        control_interface._session.decoded_access_token.hex()))
    click.echo("Open UDP Socket.")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

    try:
        frames = image.n_frames
    except:
        frames = 1
    click.echo("Frames: {}".format(frames))
    click.echo("File: {}".format(gif))
    while frames > 0:
        #for each frame in the gif
        for frame in range(0,frames):
            #click.echo("Seek to Frame: {}".format(frame))

            #seek to the frame
            image.seek(frame)
            #resize to the map
            #click.echo("Resize Frame: {}".format(frame))

            resized_im = image.resize((map_width, map_height)).convert('RGBA')

            #loop over the map
            showframe = []

            for y in range(0, map_height):
                row = []
                for x in range(0, map_width):
                    row.append(resized_im.getpixel((x,y)))

                showframe.append(row)

            #print(showframe)
            #click.echo("Create packet: {}".format(frame))

            #create a new packet
            packet = bytearray(b'\x01')
            #Add the access token
            packet.extend(control_interface._session.decoded_access_token)
            #Add the total leds
            packet.append(bytes_per_led)

            for led in range(1, number_of_led+1):
                found = 0
                #look for the led number in the map.
                for row in range(0,map_height):
                    #print(row)
                    for col in range(0,map_width):
                        #click.echo("Search Row {} and Col {} - {} ==  {} ".format(row,col,map[row][col],led))
                        if( int(map[row][col]) == led ):
                            #print("pixel found in map")
                            #print(showframe[row][col])
                            #for v in showframe[row][col]:
                            if(showframe[row][col][3]>0):
                                packet.append(showframe[row][col][0])
                                packet.append(showframe[row][col][1])
                                packet.append(showframe[row][col][2])
                            else:
                                packet.append(0)
                                packet.append(0)
                                packet.append(0)
                            found = 1
                if( found == 0 ):
                    packet.append(0)
                    packet.append(0)
                    packet.append(0)

            #click.echo("Send Packet: {}".format(frame))
            sock.sendto( packet, (control_interface.host, 7777))
            #print(image.info['duration'])
            try:
                time.sleep(image.info['duration']/1000)
            except:
                time.sleep(0.1)

@main.command(name="get-timer", help="Gets current timer settings.")
@click.pass_context
def get_timer(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Getting timer...")
    timer = control_interface.get_formatted_timer()
    click.echo("Time now: {}.".format(timer.now))
    if timer.on is False:
        click.echo("Time to turn on not set.")
    else:
        click.echo("Turn on {}.".format(timer.on))
    if timer.off is False:
        click.echo("Time to turn off not set.")
    else:
        click.echo("Turn off {}.".format(timer.off))


@main.command(name="set-timer", help="Sets timer.")
@click.argument("time-on", callback=validate_time)
@click.argument("time-off", callback=validate_time)
@click.pass_context
def set_timer(ctx, time_on, time_off):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    seconds_on = xled.util.seconds_after_midnight_from_time(*time_on)
    seconds_off = xled.util.seconds_after_midnight_from_time(*time_off)
    log.debug("Setting timer...")
    control_interface.set_timer(seconds_on, seconds_off)
    click.echo("Timer set.")


@main.command(name="disable-timer", help="Disables timer.")
@click.pass_context
def disable_timer(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Disabling timer...")
    control_interface.disable_timer()
    click.echo("Timer disabled.")


@main.command(name="get-device-name", help="Gets current device name.")
@click.pass_context
def get_device_name(ctx):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Getting device name...")
    name = control_interface.get_device_name()
    click.echo("Device name: {}".format(name["name"]))


@main.command(name="set-device-name", help="Sets device name.")
@click.argument("name")
@click.pass_context
def set_device_name(ctx, name):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Setting device name...")
    control_interface.set_device_name(name)
    click.echo("Set new name to {}".format(name))


@main.command(name="upload-movie", help="Uploads movie.")
@click.argument("movie", type=click.File("rb"))
@click.pass_context
def upload_movie(ctx, movie):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Uploading movie...")
    response = control_interface.set_led_movie_full(movie)
    click.echo("Uploaded {} frames.".format(response["frames_number"]))


@main.command(name="set-color", help="Sets static color.")
@click.argument("red", type=click.IntRange(0, 256))
@click.argument("green", type=click.IntRange(0, 256))
@click.argument("blue", type=click.IntRange(0, 256))
@click.pass_context
def set_color(ctx, red, green, blue):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    log.debug("Setting color")
    control_interface.set_static_color(red, green, blue)
    click.echo("Color set")


@main.command(name="update-firmware", help="Updates firmware.")
@click.argument("stage0", type=click.File("rb"))
@click.argument("stage1", type=click.File("rb"))
@click.pass_context
def update_firmware(ctx, stage0, stage1):
    control_interface = common_preamble(ctx.obj.get("name"), ctx.obj.get("hostname"))
    try:
        control_interface.update_firmware(stage0, stage1)
    except xled.exceptions.HighInterfaceError as hci_err:
        click.echo(hci_err, err=True)
    else:
        click.echo("Firmware update successful.")
