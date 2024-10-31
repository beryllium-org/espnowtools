rename_process("espnow")
be.api.setvar("return", "1")
vr("opts", be.api.xarg())
vr(
    "htext",
    """Usage: espnow [ OPTIONS ] COMMAND
    init                      | Initialize a ESPNow device node
    peer [ MAC ] [ KEY ]      | Add a new peer, fancy MAC, optionally accepting encryption key (string of 16)
    send [ DATA ]             | Send data to all registered peers
    key  [ KEY ]              | Set local master key (string of 16)
    deinit                    | Deinitialize the ESPNow device node
""",
)

if not vr("opts")["w"]:
    term.write(vr("htext"))
elif "init" == vr("opts")["w"][0]:
    if "ESPNow" in be.devices.keys():
        term.write("Already initialized!")
    else:
        import espnow

        be.based.run("mknod ESPNow")
        vr("node", be.api.getvar("return"))
        be.api.subscript("/bin/stringproccessing/devid.py")
        be.devices["ESPNow"][0] = espnow.ESPNow()
        del espnow
        dmtex("ESPNow: Service started.")

        class ttyESPNow:
            def __init__(self, espn):
                self._espn = espn
                self._in_buf = None

            def _rr(self) -> None:
                pak = self._espn.read()
                while pak is not None:
                    if pak[0] in [peer.mac for peer in self._espn.peers]:
                        if self._in_buf is None:
                            self._in_buf = pak[1]
                        else:
                            self._in_buf += pak[1]
                    pak = self._espn.read()

            @property
            def in_waiting(self) -> int:
                self._rr()
                return len(self._in_buf) if self._in_buf is not None else 0

            def reset_input_buffer(self) -> None:
                self._in_buf = None

            def read(self, no: int = None) -> bytes:
                res = b""
                if no is None:
                    if self.in_waiting:
                        res = self._in_buf
                        self._in_buf = None
                else:
                    while len(res) < no:
                        if self.in_waiting:
                            res += self._in_buf
                            self._in_buf = None
                    if len(res) > no:
                        self._in_buf = res[no:]
                        res = res[:no]
                return res

            def write(self, data: bytes) -> int:
                self._espn.send(data)
                return len(data)

            def deinit(self) -> None:
                if self._espn is not None:
                    self._espn = None
                    self._in_buf = None

        pv[0]["consoles"]["ttyESPNow0"] = ttyESPNow(be.devices["ESPNow"][0])
        del ttyESPNow
        dmtex("ESPNow: Console registered.")
elif "peer" == vr("opts")["w"][0]:
    if len(vr("opts")["w"]) < 2:
        term.write(vr("htext"))
    else:
        vr("ok", True)
        vr("mac_st", vr("opts")["aw"][1])
        if vr("mac_st").count(":") != 5:
            vr("ok", False)
        vr("parts", vr("mac_st").split(":"))
        for pv[get_pid()]["part"] in vr("parts"):
            if len(vr("part")) != 2:
                vr("ok", False)
            for pv[get_pid()]["char"] in vr("part"):
                if vr("char") not in "0123456789abcdefABCDEF":
                    vr("ok", False)
        if vr("ok"):
            vr("byte_parts", [])
            for pv[get_pid()]["part"] in vr("parts"):
                vra("byte_parts", int(vr("part"), 16))
            vr("mac", bytes(vr("byte_parts")))

        if vr("ok"):
            vr("enc", None)
            if len(vr("opts")["w"]) > 2:
                vr("enc", vr("opts")["w"][2])
                if len(vr("enc")) != 16:
                    term.write("Key must be exactly 16 characters!")
                    vr("ok", False)
            if vr("ok"):
                import espnow

                if vr("enc") is not None:
                    be.devices["ESPNow"][0].peers.append(
                        espnow.Peer(mac=vr("mac"), lmk=vr("enc"), encrypted=True)
                    )
                else:
                    be.devices["ESPNow"][0].peers.append(espnow.Peer(mac=vr("mac")))
                del espnow
                dmtex("ESPNow: Peer " + vr("opts")["w"][1] + " added.")
        else:
            term.write("Invalid MAC address")
elif "send" == vr("opts")["w"][0]:
    vr("dat", " ".join(vr("opts")["w"][1:]))
    if vr("dat"):
        be.devices["ESPNow"][0].send(vr("dat"))
    else:
        term.write("No data provided.")
elif "key" == vr("opts")["w"][0]:
    if len(vr("opts")["w"]) > 1:
        vr("enc", vr("opts")["w"][1])
        if len(vr("enc")) != 16:
            term.write("Key must be exactly 16 characters!")
        else:
            be.devices["ESPNow"][0].set_pmk(vr("enc"))
            dmtex("ESPNow: Encryption enabled.")
    else:
        be.devices["ESPNow"][0].set_pmk("\x00" * 16)
        dmtex("ESPNow: Encryption disabled!")
        term.write("ESPNow: Encryption disabled!")
elif "deinit" == vr("opts")["w"][0]:
    if "ESPNow" in be.devices.keys():
        be.devices["ESPNow"][0].deinit()
        be.based.run("rmnod ESPNow0")
        dmtex("ESPNow: Service stopped.")
        del pv[0]["consoles"]["ttyESPNow0"]
        dmtex("ESPNow: Console removed.")
else:
    term.write(vr("htext"))
