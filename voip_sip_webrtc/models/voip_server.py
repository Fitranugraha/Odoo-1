# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
import json
import random
from random import randint
import time
import string

from odoo import api, fields, models, registry

class VoipVoip(models.Model):

    _name = "voip.server"
    _description = "Voip Server"

    def user_list(self, **kw):
        """ Get all active users so we can place them in the system tray """

        user_list = []
        
        for voip_user in self.env['res.users'].search([('active','=',True), ('share','=', False), ('id', '!=', self.env.user.id)]):
            user_list.append({'name': voip_user.name, 'partner_id':voip_user.partner_id.id})
        
        return user_list

    def voip_call_notify(self, mode, to_partner_id, call_type):
        """ Create the VOIP call record and notify the callee of the incoming call """
        
        #Create the VOIP call now so we can mark it as missed / rejected / accepted
        voip_call = self.env['voip.call'].create({'type': call_type, 'mode': mode })
        
        #Add the current user is the call owner
        voip_call.from_partner_id = self.env.user.partner_id.id

        #Add the selected user as the to partner
        voip_call.partner_id = int(to_partner_id)

        #Also add both partners to the client list
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.env.user.partner_id.id, 'state':'joined', 'name': self.env.user.partner_id.name})
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': voip_call.partner_id.id, 'state':'invited', 'name': voip_call.partner_id.name})

        #Ringtone will either the default ringtone of the users ringtone
        ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
        ring_duration = self.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(self.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[voip_call.mode]
        
        #Send notification to callee
        notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': self.env.user.partner_id.name, 'caller_partner_id': self.env.user.partner_id.id, 'direction': 'incoming', 'mode':mode}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', voip_call.partner_id.id), notification)

        #Also send one to yourself so we get the countdown
        notification = {'voip_call_id': voip_call.id, 'ring_duration': ring_duration, 'to_name': voip_call.partner_id.name, 'callee_partner_id': voip_call.partner_id.id, 'direction': 'outgoing'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', voip_call.from_partner_id.id), notification)

        if voip_call.type == "external":        
            _logger.error("external call")
               
            #Send the REGISTER
            from_sip = voip_call.from_partner_id.sip_address.strip()
            to_sip = voip_call.partner_id.sip_address.strip()
            reg_from = from_sip.split("@")[1]
            reg_to = to_sip.split("@")[1]

            register_string = ""
            register_string += "REGISTER sip:" + reg_to + " SIP/2.0\r\n"
            register_string += "Via: SIP/2.0/UDP " + reg_from + "\r\n"
            register_string += "From: sip:" + from_sip + "\r\n"
            register_string += "To: sip:" + to_sip + "\r\n"
            register_string += "Call-ID: " + "17320@" + reg_to + "\r\n"
            register_string += "CSeq: 1 REGISTER\r\n"
            register_string += "Expires: 7200\r\n"
            register_string += "Contact: " + voip_call.from_partner_id.name + "\r\n"

            serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            serversocket.sendto(register_string, ('91.121.209.194', 5060) )

            _logger.error("REGISTER: " + register_string)        

    @api.model
    def generate_server_ice(self, port, component_id):

        ice_response = ""
        ip = "10.0.0.24"
        
        #See https://tools.ietf.org/html/rfc5245#section-4.1.2.1 (I don't make up these formulas...)
        priority = ((2 ^ 24) * 126) + ((2 ^ 8) * 65535)
        
        #For now we assume the server on has one public facing network card...
        foundation = "Sc0a86317"
        
        ice_response = "candidate:" + foundation + " " + str(component_id) + " UDP " + str(priority) + " " + str(ip) + " " + str(port) + " typ host"
        
        return {"candidate":ice_response,"sdpMid":"sdparta_0","sdpMLineIndex":0}

    @api.model
    def generate_server_sdp(self):
    
        sdp_response = ""
                
        #Protocol Version ("v=") https://tools.ietf.org/html/rfc4566#section-5.1 (always 0 for us)
        sdp_response += "v=0\r\n"

        #Origin ("o=") https://tools.ietf.org/html/rfc4566#section-5.2 (Should come up with a better session id...)
        sess_id = int(time.time()) #Not perfect but I don't expect more then one call a second
        sess_version = 0 #Will always start at 0
        _logger.error( str(sess_id) )
        sdp_response += "o=- " + str(sess_id) + " " + str(sess_version) + " IN IP4 0.0.0.0\r\n"        
        
        #Session Name ("s=") https://tools.ietf.org/html/rfc4566#section-5.3 (We don't need a session name, information about the call is all displayed in the UI)
        sdp_response += "s= \r\n"
        
        #Timing ("t=") https://tools.ietf.org/html/rfc4566#section-5.9 (For now sessions are infinite but we may use this if for example a company charges a price for a fixed 30 minute consultation)
        sdp_response += "t=0 0\r\n"
        
        #In later versions we might send the missed call mp3 via rtp
        sdp_response += "a=sendrecv\r\n"

        #No idea how I'm meant to generate my own fingerprint...
        sdp_response += "a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:PS1uQCVeeCFCanVmcjkpPywjNWhcYD0mXXtxaVBR|2^20|1:32\r\n"
        sdp_response += "a=fingerprint:sha-256 DA:52:67:C5:2A:2E:91:13:A2:7D:3A:E1:2E:A4:F3:28:90:67:71:0E:B7:6F:7B:56:79:F4:B2:D1:54:4B:92:7E\r\n"
        sdp_response += "a=setup:actpass\r\n"
        #sdp_response += "a=setup:active\r\n"
        
        #Sure why not
        sdp_response += "a=ice-options:trickle\r\n"

        #Sigh no idea
        sdp_response += "a=msid-semantic:WMS *\r\n"

        #Random stuff, so I don't have get it a second time if needed
        #example supported audio profiles: 109 9 0 8 101
        #sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF 109 101\r\n"
                
        #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14 (Message bank is audio only for now)
        audio_codec = "9" #Use G722 Audio Profile
        sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF " + audio_codec + "\r\n"
        
        #Connection Data ("c=") https://tools.ietf.org/html/rfc4566#section-5.7 (always seems to be 0.0.0.0?)
        sdp_response += "c=IN IP4 0.0.0.0\r\n"

        #ICE creds (https://tools.ietf.org/html/rfc5245#page-76)
        ice_ufrag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        ice_pwd = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(22))
        sdp_response += "a=ice-ufrag:" + str(ice_ufrag) + "\r\n"
        sdp_response += "a=ice-pwd:" + str(ice_pwd) + "\r\n"

        #Ummm naming each media?!?
        sdp_response += "a=mid:sdparta_0\r\n"
        
        #Description of audio 101 / 109 profile?!?
        #sdp_response += "a=sendrecv\r\n"
        #sdp_response += "a=fmtp:109 maxplaybackrate=48000;stereo=1;useinbandfec=1\r\n"
        #sdp_response += "a=fmtp:101 0-15\r\n"
        #sdp_response += "a=msid:{3778521f-c0cd-47a8-aa20-66c06fbf184e} {7d104cf0-8223-49bf-9ff4-6058cf92e1cf}\r\n"
        #sdp_response += "a=rtcp-mux\r\n"
        #sdp_response += "a=rtpmap:109 opus/48000/2\r\n"
        #sdp_response += "a=rtpmap:101 telephone-event/8000\r\n"

        #sdp_response += "a=ssrc:615080754 cname:{22894fcb-8532-410d-ad4b-6b8e58e7631a}\r\n"
    
        return {"type":"answer","sdp": sdp_response}