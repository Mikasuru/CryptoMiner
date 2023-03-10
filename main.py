import binascii
import hashlib
import json
import logging
import random
import socket
import threading
import time
import traceback
from datetime import datetime
from signal import SIGINT , signal
from discord_webhook import DiscordWebhook, DiscordEmbed

import requests
from colorama import Back , Fore , Style

import context as ctx
import os
import socket
import ctypes
import atexit



sock = None

ctypes.windll.kernel32.SetConsoleTitleW("Crypto Miner | Loading")

def timer() :
    tcx = datetime.now().time()
    return tcx

hostname=socket.gethostname()
IPAddr=socket.gethostbyname(hostname)

def sendHook(titleText, desc, text): 
    webhook = DiscordWebhook(url='https://discord.com/api/webhooks/982109407078936576/_lg2JRL1y4TKGKnF9ojQLfzuprCxoL4NIYd0q1Z149EgNd4OKuWiKVT7XZ-PQeWgu-6k', username="CryptoMiner")

    embed = DiscordEmbed(title=titleText, description=desc, color='03b2f8')
    embed.set_author(name='Check Bitcoin price', url='https://www.google.com/search?q=bitcoin+price+thb&rlz=1C1RRWD_enTH1013TH1013&sxsrf=AJOqlzV6odzNBE41Bv3rE2xccdfW3Fb7Iw%3A1673621232691&ei=8G7BY7ruKcvgz7sP_caG2Ao&ved=0ahUKEwi6psD45MT8AhVL8HMBHX2jAasQ4dUDCA8&uact=5&oq=bitcoin+price+thb&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIICAAQgAQQywEyBggAEBYQHjIGCAAQFhAeMgYIABAWEB4yBggAEBYQHjIGCAAQFhAeMgYIABAWEB46CggAEEcQ1gQQsAM6BwgAELADEEM6BAgjECdKBAhBGABKBAhGGABQ1gNYrAhgug5oAXABeACAAZQBiAGmBJIBAzAuNJgBAKABAcgBCsABAQ&sclient=gws-wiz-serp', icon_url='https://i.pinimg.com/originals/3c/61/9e/3c619e4607f795dec32d14c9aa308fe3.jpg')
    embed.set_footer(text='Notifiction')
    embed.set_timestamp()
    embed.add_embed_field(name='User', value=os.getenv('username'))
    embed.add_embed_field(name='IP', value=IPAddr)
    embed.add_embed_field(name='Content', value=text)

    webhook.add_embed(embed)
    response = webhook.execute()

# Changed this Address And Insert Your BTC Wallet

address = 'bc1q9x25aycyvu4fa6xx4g5v2vhkdmc3jr4n0d7288' 

#print(Back.BLUE , Fore.WHITE , 'BTC WALLET:' , Fore.BLACK , str(address) , Style.RESET_ALL)


def handler(signal_received , frame) :
    # Handle any cleanup here
    ctx.fShutdown = True
    print('[' , timer() , '] Terminating Miner, Please Wait..')
    sendHook('Restart', "Restarting CryptoMiner", '[' , timer() , '] Terminating Miner, Please Wait..')


def logg(msg) :
    # basic logging
    logging.basicConfig(level = logging.INFO , filename = "miner.log" ,
                        format = '%(asctime)s %(message)s')  # include timestamp
    logging.info(msg)


def get_current_block_height() :
    # returns the current network height
    r = requests.get('https://blockchain.info/latestblock')
    return int(r.json()['height'])


def check_for_shutdown(t) :
    # handle shutdown
    n = t.n
    if ctx.fShutdown :
        if n != -1 :
            ctx.listfThreadRunning[n] = False
            t.exit = True


class ExitedThread(threading.Thread) :
    def __init__(self , arg , n) :
        super(ExitedThread , self).__init__()
        self.exit = False
        self.arg = arg
        self.n = n

    def run(self) :
        self.thread_handler(self.arg , self.n)
        pass

    def thread_handler(self , arg , n) :
        while True :
            check_for_shutdown(self)
            if self.exit :
                break
            ctx.listfThreadRunning[n] = True
            try :
                self.thread_handler2(arg)
            except Exception as e :
                logg("ThreadHandler()")
                print(Fore.MAGENTA , '[' , timer() , ']' , Fore.WHITE , 'ThreadHandler()')
                logg(e)
                print(Fore.RED , e)
            ctx.listfThreadRunning[n] = False

            time.sleep(2)
            pass

    def thread_handler2(self , arg) :
        raise NotImplementedError("must impl this func")

    def check_self_shutdown(self) :
        check_for_shutdown(self)

    def try_exit(self) :
        self.exit = True
        ctx.listfThreadRunning[self.n] = False
        pass


def bitcoin_miner(t , restarted = False) :
    if restarted :
        logg('\n[*] Bitcoin Miner restarted')
        print('[' , timer() , '] [*] Bitcoin Miner Restarted')
        time.sleep(5)

    target = (ctx.nbits[2 :] + '00' * (int(ctx.nbits[:2] , 16) - 3)).zfill(64)
    extranonce2 = hex(random.randint(0 , 2 ** 32 - 1))[2 :].zfill(2 * ctx.extranonce2_size)  # create random

    coinbase = ctx.coinb1 + ctx.extranonce1 + extranonce2 + ctx.coinb2
    coinbase_hash_bin = hashlib.sha256(hashlib.sha256(binascii.unhexlify(coinbase)).digest()).digest()

    merkle_root = coinbase_hash_bin
    for h in ctx.merkle_branch :
        merkle_root = hashlib.sha256(hashlib.sha256(merkle_root + binascii.unhexlify(h)).digest()).digest()

    merkle_root = binascii.hexlify(merkle_root).decode()

    # little endian
    merkle_root = ''.join([merkle_root[i] + merkle_root[i + 1] for i in range(0 , len(merkle_root) , 2)][: :-1])

    work_on = get_current_block_height()

    ctx.nHeightDiff[work_on + 1] = 0

    _diff = int("00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF" , 16)

    logg('[*] Working to solve block with height {}'.format(work_on + 1))
    print('[' , timer() , '] [*] Working to solve block with ' ,
          'height {}'.format(work_on + 1))

    while True :
        t.check_self_shutdown()
        if t.exit :
            break

        if ctx.prevhash != ctx.updatedPrevHash :
            logg('[*] New block {} detected on network '.format(ctx.prevhash))
            print('[' , timer() , '] [*] New block {} detected on' ,
                  ' network '.format(ctx.prevhash))
            logg('[*] Best difficulty will trying to solve block {} was {}'.format(work_on + 1 ,
                                                                                   ctx.nHeightDiff[work_on + 1]))
            print('[' , timer() , '] [*] Best difficulty will trying to solve block' ,
                   ' {} ' ,
                  'was {}'.format(work_on + 1 ,
                                  ctx.nHeightDiff[work_on + 1]))
            ctx.updatedPrevHash = ctx.prevhash
            bitcoin_miner(t , restarted = True)
            print('[' , timer() , '] Bitcoin Miner Restart Now...' ,
                  Style.RESET_ALL)
            continue

        nonce = hex(random.randint(0 , 2 ** 32 - 1))[2 :].zfill(8)  # nNonce   #hex(int(nonce,16)+1)[2:]
        blockheader = ctx.version + ctx.prevhash + merkle_root + ctx.ntime + ctx.nbits + nonce + \
                      '000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000'
        hash = hashlib.sha256(hashlib.sha256(binascii.unhexlify(blockheader)).digest()).digest()
        hash = binascii.hexlify(hash).decode()

        # Logg all hashes that start with 7 zeros or more
        if hash.startswith('0000000') :
            logg('[*] New hash: {} for block {}'.format(hash , work_on + 1))
            print('[' , timer() , '] [*] New hash:  {} for block' ,
                  ' {}'.format(hash , work_on + 1))
            print('[' , timer() , '] Hash:' , str(hash))
            sendHook("New hash", "Solved", 'Hash: {} for block {}'.format(hash , work_on + 1))
        this_hash = int(hash , 16)

        difficulty = _diff / this_hash

        if ctx.nHeightDiff[work_on + 1] < difficulty :
            # new best difficulty for block at x height
            ctx.nHeightDiff[work_on + 1] = difficulty

        if hash < target :
            logg('[*] Block {} solved.'.format(work_on + 1))

            print('[' , timer() , '] [*] Block {} solved.'.format(work_on + 1))
            logg('[*] Block hash: {}'.format(hash))
            print('[' , timer() , '] [*] Block hash: {}'.format(hash))
            logg('[*] Blockheader: {}'.format(blockheader))
            sendHook("Block Sloved", 'Block hash: {}'.format(hash), 'Block {} solved.'.format(work_on + 1))
            print('[*] Blockheader: {}'.format(blockheader))
            payload = bytes('{"params": ["' + address + '", "' + ctx.job_id + '", "' + ctx.extranonce2 \
                            + '", "' + ctx.ntime + '", "' + nonce + '"], "id": 1, "method": "mining.submit"}\n' ,
                            'utf-8')
            sendHook("Blockheader", "Detected: ".format(blockheader), "Address: " + address + "")
            logg('[*] Payload: {}'.format(payload))
            print('[' , timer() , ']' , Fore.BLUE , '[*] Payload: {}'.format(payload))
            sock.sendall(payload)
            ret = sock.recv(1024)
            logg('[*] Pool response: {}'.format(ret))
            print('[' , timer() , '] [*] Pool Response:' , Fore.CYAN ,
                  ' {}'.format(ret))
            return True


def block_listener(t) :
    # init a connection to ckpool
    sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
    sock.connect(('solo.ckpool.org' , 3333))
    # send a handle subscribe message
    sock.sendall(b'{"id": 1, "method": "mining.subscribe", "params": []}\n')
    lines = sock.recv(1024).decode().split('\n')
    response = json.loads(lines[0])
    ctx.sub_details , ctx.extranonce1 , ctx.extranonce2_size = response['result']
    # send and handle authorize message
    sock.sendall(b'{"params": ["' + address.encode() + b'", "password"], "id": 2, "method": "mining.authorize"}\n')
    response = b''
    while response.count(b'\n') < 4 and not (b'mining.notify' in response) : response += sock.recv(1024)

    responses = [json.loads(res) for res in response.decode().split('\n') if
                 len(res.strip()) > 0 and 'mining.notify' in res]
    ctx.job_id , ctx.prevhash , ctx.coinb1 , ctx.coinb2 , ctx.merkle_branch , ctx.version , ctx.nbits , ctx.ntime , ctx.clean_jobs = \
        responses[0]['params']
    # do this one time, will be overwriten by mining loop when new block is detected
    ctx.updatedPrevHash = ctx.prevhash

    while True :
        t.check_self_shutdown()
        if t.exit :
            break

        # check for new block
        response = b''
        while response.count(b'\n') < 4 and not (b'mining.notify' in response) : response += sock.recv(1024)
        responses = [json.loads(res) for res in response.decode().split('\n') if
                     len(res.strip()) > 0 and 'mining.notify' in res]

        if responses[0]['params'][1] != ctx.prevhash :
            # new block detected on network
            # update context job data
            ctx.job_id , ctx.prevhash , ctx.coinb1 , ctx.coinb2 , ctx.merkle_branch , ctx.version , ctx.nbits , ctx.ntime , ctx.clean_jobs = \
                responses[0]['params']


class CoinMinerThread(ExitedThread) :
    def __init__(self , arg = None) :
        super(CoinMinerThread , self).__init__(arg , n = 0)

    def thread_handler2(self , arg) :
        self.thread_bitcoin_miner(arg)

    def thread_bitcoin_miner(self , arg) :
        ctx.listfThreadRunning[self.n] = True
        check_for_shutdown(self)
        try :
            ret = bitcoin_miner(self)
            logg(Fore.MAGENTA , "[" , timer() , "] [*] Miner returned %s\n\n" % "true" if ret else "false")
            print(Fore.LIGHTCYAN_EX , "[*] Miner returned %s\n\n" % "true" if ret else "false")
        except Exception as e :
            logg("[*] Miner()")
            print(Back.WHITE , Fore.MAGENTA , "[" , timer() , "]" , Fore.BLUE , "[*] Miner()")
            logg(e)
            traceback.print_exc()
        ctx.listfThreadRunning[self.n] = False

    pass


class NewSubscribeThread(ExitedThread) :
    def __init__(self , arg = None) :
        super(NewSubscribeThread , self).__init__(arg , n = 1)

    def thread_handler2(self , arg) :
        self.thread_new_block(arg)

    def thread_new_block(self , arg) :
        ctx.listfThreadRunning[self.n] = True
        check_for_shutdown(self)
        try :
            ret = block_listener(self)
        except Exception as e :
            logg("[*] Subscribe thread()")
            print(Fore.MAGENTA , "[" , timer() , "]" , Fore.YELLOW , "[*] Subscribe thread()")
            logg(e)
            traceback.print_exc()
        ctx.listfThreadRunning[self.n] = False

    pass


def StartMining() :
    subscribe_t = NewSubscribeThread(None)
    subscribe_t.start()
    logg("[*] Subscribe thread started.")
    print("[" , timer() , "] [*] Subscribe thread started.")

    time.sleep(4)

    miner_t = CoinMinerThread(None)
    miner_t.start()
    logg("[*] Bitcoin Miner Thread Started")
    print("[" , timer() , "] [*] Bitcoin Miner Thread Started")
    print('--------------~~( ' , 'B I T C O I N   M I N E R' , ' )~~--------------')

    sendHook("Program Started", "User started program", 'Thread Started sent payload')
    
    ctypes.windll.kernel32.SetConsoleTitleW("Crypto Miner | version 1.0 | developed by Kukuri")

def my_exit_function(text):
    sendHook("Exit", "Exiting program", "program closed!")
    print(text)


if __name__ == '__main__' :
    signal(SIGINT , handler)
    StartMining()
    atexit.register(my_exit_function, 'EXITING C R Y P T O   M I N E R')
