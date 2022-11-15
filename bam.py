import asyncio, time

from irctokens import build, Line
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams

from secrets import OPER, NICK, NETWORK, HOST, SECONDS, MAXMSGS, JOIN, BADLINE, KILL, LOG


class Server(BaseServer):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.log={}
        self.isoper=[]
    async def line_read(self, line):
        print(f"{self.name} < {line.format()}")
        if "on_" + line.command.lower() in dir(self):
            asyncio.create_task(
                self.__getattribute__("on_" + line.command.lower())(line)
            )

    # disable automatic WHOing
    async def _next_who(self):
        pass

    async def line_send(self, line):
        print(f"{self.name} > {line.format()}")

    async def on_001(self, line):
        await self.send_raw(OPER)

    async def on_313(self, line):
        self.isoper.append(line.params[1])

    async def on_378(self, line):
        if line.params[1] in self.isoper:
            self.isoper.remove(line.params[1])
            return
        username = self.users[line.params[1]].username
        if username[0] == '~':
            username = '*'
        await self.send_raw(KILL.format(line.params[1]))
        await self.send_raw(BADLINE.format(username, line.params[2].split()[3][2:]))
        await self.send_raw(BADLINE.format(username, line.params[2].split()[4]))

    async def on_privmsg(self, line):
        nick = line.hostmask.nickname
        if nick not in self.log:
            self.log[nick] = []

        self.log[nick].append([time.time()] + line.params)
        if len(self.log[nick]) > MAXMSGS:
            self.log[nick].pop(0)
        elif len(self.log[nick]) < MAXMSGS:
            return

        if self.log[nick][0][0] + SECONDS <= time.time():
            self.log[nick].pop(0)
            return

        channels = []
        for msg in self.log[nick][:-1]:
            channels.append(msg[1])
            if msg[2] != line.params[1]:
                return

        if len(set(channels)) < 2:
            return

        await self.send(build("WHOIS",[nick,nick]))
        await self.send_raw(LOG.format(nick,','.join(set([ln[1] for ln in self.log[nick]]))))

        del self.log[nick]

    async def on_invite(self, line):
        await self.send(build("JOIN",[line.params[1]]))

class Bot(BaseBot):
    def create_server(self, name: str):
        return Server(self, name)


async def main():
    bot = Bot()

    params = ConnectionParams(NICK, host=HOST, port=6697, autojoin=JOIN)

    await bot.add_server(NETWORK, params)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
