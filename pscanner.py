#!/usr/bin/python

import sys
import urwid
import os

import argparse

import multiprocessing

import ssl
import socket
from socket import gethostbyname, gaierror

from dns import reversename, resolver, exception
import sys

import M2Crypto
from embparpbar import ProgressPool


import pprint

class SwitchingPadding(urwid.Padding):
    def padding_values(self, size, focus):
        maxcol = size[0]
        width, ignore = self.original_widget.pack(size, focus=focus)
        if maxcol > width:
            self.align = "left"
        else:
            self.align = "right"
        return urwid.Padding.padding_values(self, size, focus)


def scan_nossl(d):
          di.scan_box.base_widget.set_text("Scanning: "+d)
          di.loop.draw_screen()
          d=str(d)
          try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            result = s.connect_ex((d, int(port)))
            s.close()
          except Exception, e:
            message = "Error: "+d.rstrip()+","+getrev(d)
            message += str(e)
            return message
          if result:
            return d.rstrip()+","+port+",closed"
          else:
            return d.rstrip()+","+port+",open"
          

def scan_ssl(d):
          s_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s = ssl.wrap_socket(s_, ca_certs='/usr/local/lib/python2.7/dist-packages/requests/cacert.pem',cert_reqs=ssl.CERT_OPTIONAL)

          s.settimeout(0.1)
          d=str(d)
          try:
            result = s.connect_ex((d, int(port)))
          except Exception, e:
                message = "Error: "+d.rstrip()+","+getrev(d)
                message += str(e)
                try:
                  cert = ssl.get_server_certificate((d, 443), ssl_version=ssl.PROTOCOL_TLSv1)
                  x509 = M2Crypto.X509.load_cert_string(cert)
                  r = x509.get_subject().as_text()
                  val = r.split(",")
                  for i, j in enumerate(val):
                    if j.find("CN=") != -1:
                      val[i]=j.replace("CN=","")
                      val[i]=val[i].strip()
                  message += ","+val[i]
                  return message
                except Exception, e:
                       return d.rstrip()+","+getrev(d)+","+"CERT ERROR!"
          except ssl.SSLError:
            return d.rstrip()+","+getrev(d)+","+"CERT ERROR!"
          except socket.gaierror:
            return d.rstrip()+","+"SOCKET ERROR!"
          except socket.error:
            return d.rstrip()+","+"SOCKET ERROR!"
          if result:
            return "No SSL"
          else:
            cert = s.getpeercert()
            if cert:
              subject = dict(x[0] for x in cert['subject'])
              issued_to = subject['commonName']
            else:
              subject = "None"
              issued_to = "None"
            return d.rstrip()+","+getrev(d)+","+"CN:"+issued_to+","+"CERT OK"





def getrev(ip):

      try:
        rev_name = reversename.from_address(str(ip.rstrip()))
        resolverobj = resolver.Resolver()
        resolverobj.timeout = 1
        resolverobj.lifetime = 1
        reversed_dns = str(resolverobj.query(rev_name,"PTR")[0])
        reversed_dns = reversed_dns[:-1]
        return reversed_dns
      except resolver.NXDOMAIN:
        return "unknown"
      except resolver.Timeout:
        return "Timed out while resolving %s" % ip.rstrip()
      except exception.DNSException:
        return "Unhandled exception"



class DialogExit(Exception):
    pass


class DialogDisplay:
    palette = [
        ('body','black','light gray', 'standout'),
        ('border','black','dark blue'),
        ('shadow','white','black'),
        ('selectable','black', 'dark cyan'),
        ('focus','white','dark blue','bold'),
        ('focustext','light gray','dark blue'),
        ]
    

    def __init__(self, text, height, width, body=None):
        self.bar1 = urwid.ProgressBar('pg normal', 'pg complete')
        # Create BigText
        bt = urwid.BigText("pScanner",  urwid.font.Thin6x6Font())
        bt = urwid.Padding(bt, 'left', width='clip')
        bt = urwid.Filler(bt, 'bottom')
        bt = urwid.BoxAdapter(bt, 7)

        self.scan_box = urwid.Text("")
        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.body = body
        if body is None:
            # fill space with nothing
            body = urwid.Filler(urwid.Divider(),'top')

        self.frame = urwid.Frame( body, focus_part='footer')
        if text is not None:
            self.frame.header = urwid.Pile( [ urwid.Text(text), bt,
                urwid.Divider(), self.bar1, urwid.Divider(), self.scan_box] )

        # Adding progressbar

        #self.frame = urwid.Frame(urwid.ListBox([bar1]))

        w = self.frame

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left',2), ('fixed right',2))
        w = urwid.Filler(w, ('fixed top',1), ('fixed bottom',1))
        w = urwid.AttrWrap(w, 'body')

        # "shadow" effect
        w = urwid.Columns( [w,('fixed', 2, urwid.AttrWrap(
            urwid.Filler(urwid.Text(('border','  ')), "top")
            ,'shadow'))])
        w = urwid.Frame( w, footer =
            urwid.AttrWrap(urwid.Text(('border','  ')),'shadow'))

        # outermost border area
        w = urwid.Padding(w, 'center', width )
        w = urwid.Filler(w, 'middle', height )
        w = urwid.AttrWrap( w, 'border' )

        self.view = w


    def add_buttons(self, buttons):
        l = []
        for name, exitcode in buttons:
            if name=="Exit":
              b = urwid.Button( name, self.button_press_stop )
              b.exitcode = exitcode
            if name=="Start":
              b = urwid.Button( name, self.button_press_start )
              b.exitcode = exitcode
            b = urwid.AttrWrap( b, 'selectable','focus' )
            l.append( b )
        self.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        self.frame.footer = urwid.Pile( [ urwid.Divider(),
            self.buttons ], focus_item = 1)

    def button_press_stop(self, button):
        raise DialogExit(button.exitcode)


    def button_press_start(self, button):
        self.do_scan()




    def do_scan(self):
       global port

       parser = argparse.ArgumentParser(description='Port Scanner v0.99')
       parser.add_argument('-i','--input', help='Input list of IPs', required=True)
       parser.add_argument('-o','--output', help='Output', required=True)
       parser.add_argument('-p','--port', help='Port number(s)', required=True)
       parser.add_argument('-s','--ssl', help='SSL yes|no', required=True)
       args = parser.parse_args()
       input = args.input
       output = args.output
       port = args.port
       sslp = args.ssl
       data = open(input,'rU')
       # Create pool (ppool)
       ppool = ProgressPool(self.bar1,self.loop)

       def process_results(results):
           
           resfile = open(output,'w')
           for r in results:
               resfile.write(r+"\n")

       if(sslp=="yes"):
         results = ppool.map(scan_ssl, data, callback=process_results)
       else:
         results = ppool.map(scan_nossl, data, callback=process_results)

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.palette)
        try:

           self.loop.run()
        except DialogExit, e:
            return self.on_exit( e.args[0] )

    def on_exit(self, exitcode):
        return exitcode, ""




def main():

    global di

    di = DialogDisplay( "pScanner v0.99", 50, 50)
    di.add_buttons([    ("Exit", 0), ("Start", 0) ])


    # Run it
    exitcode, exitstring = di.main()

    # Exit
    if exitstring:
        sys.stderr.write(exitstring+"\n")

    sys.exit(exitcode)


if __name__=="__main__":
    main()
