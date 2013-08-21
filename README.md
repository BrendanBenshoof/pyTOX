pyTOX
=======

An encrypted p2p chat program
Proof of concept to build distributed applications using our chronus framework
based on work here: https://github.com/irungentoo/ProjectTox-Core/blob/master/README.md

So, what can you use this for?

It allows your to talk in "secure" distributedly hosted channels.
The defautl channel is "dev" right now and pyTOX connects to it automatically
on startup.

Secure p2p chat using RSA and DES without having to keep track of IPs
(in fact nobody can tell which IP in the network is yours without a lot of work)

Be portable, if you copy your userinfo file then you can use the client/server on multiple machines

currently stable to use, just not fun to use yet

how to install:
    git clone https://github.com/BrendanBenshoof/pyTOX.git
    
how to use:
    ./pyTOX (launches using a random port and the default seed node chronus.cs.gsu.edu)
    ./pyTOX <portnumber> (launches using the given port. This is usefull so you can setup firewall exceptions and port forwarding)
    ./pyTOX <portnumber> <IP of seed node> <port on seed node> (this lets you pick your port and connect to a specific seed node. This is usefull for when chronus is down)

using the program: (this is the rip from /help in pyTOX)
If you type without a "/" then it just sends the line to whatever chat context you are in (by default channel "dev")
You can change this context by using /chat or /chan

commands:
/chat $friendname       --- Directs all input as chat to given friend

/chan $channame         --- Directs all input to the given channel
                            listens to the channel if you are not already

/add $userinfopack      --- given the massive pile of encoded RSA key info 
                            for a user, it adds them as a friend

/listen $channame       --- adds the channel to the list you listen to

/rename $oldnic $newnic --- renames a friend (only shows change in chats
                            not channels)

/ping $friend           --- sends a ping to check if a friend is online

/who                    --- pings all your friends

/whoami                 --- prints the string you need to give other 
                        users in order to add you as a friend


currently running an etry point at 131.96.131.124 9000
