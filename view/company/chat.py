# coding: utf-8

from .__init__ import *

class ChatBuffer(object):
    def __init__(self):
        self.clients = {}

global_chat_buffer = ChatBuffer()

class WSTicket(WebSocketHandler, BaseHandler):

    def broadcast(self, message):
        ticket_id = global_chat_buffer.clients.get(self.request.headers.get('Sec-Websocket-Key'))
        if ticket_id:
            ticket_id = ticket_id.get('ticket')
        for i in global_chat_buffer.clients.keys():
            if global_chat_buffer.clients[i]['uid'] != self.current_user.get('id'):
                if global_chat_buffer.clients[i]['ticket'] == ticket_id:
                    global_chat_buffer.clients[i]['ws'].write_message("%s" % message)

    @tornado.web.authenticated # TODO: change this to use custom checks
    def open(self, tid):
        global_chat_buffer.clients[self.request.headers.get('Sec-Websocket-Key')] = {
            'ws': self, 'ticket': tid, 'uid': self.current_user.get('id')}
        self.broadcast("%s has joined chat." % (self.current_user.get('name'), ))

    def on_message(self, message):
        self.broadcast("%s: %s" % (self.current_user.get('name'), message))

    def on_close(self):
        self.broadcast("%s has left chat." % (self.current_user.get('name'), ))
        try:
            global_chat_buffer.clients.pop(self.request.headers.get('Sec-Websocket-Key'))
        except:
            logging.error("Couldn't pop websocket session id: %s" % self.request.headers.get('Sec-Websocket-Key'))

    def on_connection_close(self):
        self.broadcast("%s has left chat." % (self.current_user.get('name'), ))
        try:
            global_chat_buffer.clients.pop(self.request.headers.get('Sec-Websocket-Key'))
        except:
            logging.error("Couldn't pop websocket session id: %s" % self.request.headers.get('Sec-Websocket-Key'))

class AgentBuffer(object):
    def __init__(self):
        self.clients = {}

    def broadcast(self, message={}):
        for i in self.clients.keys():
            #self.clients[i]['ws'].write_message(str(message) + " -> " + str(self.clients[i]))
            if int(self.clients[i]['cid']) == message.get('company_id'):
                if int(self.clients[i]['did']) == message.get('department_id'):
                    self.clients[i]['ws'].write_message(json.dumps({
                        'type': 'ticket',
                        'message': message.get('ticket'),
                        'status': message.get('status'),
                    }))

global_agent_buffer = AgentBuffer()

class WSAgent(WebSocketHandler, BaseHandler):

    @tornado.web.authenticated
    def open(self):
        global_agent_buffer.clients[self.request.headers.get('Sec-Websocket-Key')] = {
            'ws': self, 'agent': self.current_user.get('id'),
            'cid': self.current_user.get('company_id'),
            'did': self.current_user.get('department_id')
        }

    def on_message(self, message):
        pass

    def on_close(self):
        try:
            global_agent_buffer.clients.pop(self.request.headers.get('Sec-Websocket-Key'))
        except:
            logging.error("Couldn't pop websocket session id: %s" % self.request.headers.get('Sec-Websocket-Key'))

    def on_connection_close(self):
        try:
            global_agent_buffer.clients.pop(self.request.headers.get('Sec-Websocket-Key'))
        except:
            logging.error("Couldn't pop websocket session id: %s" % self.request.headers.get('Sec-Websocket-Key'))
