from dnslib import DNSRecord, DNSHeader, DNSBuffer, DNSQuestion, RR, QTYPE, RCODE
from socket import socket, SOCK_DGRAM, AF_INET

"""
There are 13 root servers defined at https://www.iana.org/domains/root/servers
"""

ROOT_SERVER = "199.7.83.42"    # ICANN Root Server
DNS_PORT = 53

def get_dns_record(udp_socket, domain:str, parent_server: str, record_type):
  q = DNSRecord.question(domain, qtype = record_type)
  q.header.rd = 0   # Recursion Desired?  NO
  print("DNS query", repr(q))
  udp_socket.sendto(q.pack(), (parent_server, DNS_PORT))
  pkt, _ = udp_socket.recvfrom(8192)
  buff = DNSBuffer(pkt)
  
  """
  RFC1035 Section 4.1 Format
  
  The top level format of DNS message is divided into five sections:
  1. Header
  2. Question
  3. Answer
  4. Authority
  5. Additional
  """
  answer, authority, additional = [], [], []

  header = DNSHeader.parse(buff)
  print("DNS header", repr(header))
  if q.header.id != header.id:
    print("Unmatched transaction")
    return None
  if header.rcode != RCODE.NOERROR:
    print("Name server can't answer")
    print(f"The domain '{domain} may not exist")
    return None
       

  # Parse the question section #2
  for k in range(header.q):
    q = DNSQuestion.parse(buff)
    
     
  # Parse the answer section #3
  for k in range(header.a):
    a = RR.parse(buff)
    answer.append(a)
    
      
      
  # Parse the authority section #4
  for k in range(header.auth):
    auth = RR.parse(buff)
    authority.append(auth)
    
      
  # Parse the additional section #5
  for k in range(header.ar):
    adr = RR.parse(buff)
    additional.append(adr)


  return {"answer": answer, "authority": authority, "additional": additional}

def add_to_cache(domain, record_type, record_value):
  if domain not in cache:
    cache[domain] = dict()
  if record_type == QTYPE.NS:
    cache[domain]["NS"] = str(record_value)
  if record_type == QTYPE.A:
    cache[domain]["A"] = str(record_value)
  
def start_server(sock, domain:str, cache:dict):
  if not domain.endswith('.'):
      domain += '.'
  
  NS = ROOT_SERVER

  while True:
    record = get_dns_record(sock, domain, NS, "A")

    if record is None:
      print(f"Failed to resolve the '{domain}'- no data was returned for this.")
      return None
    
    if not record["answer"] and not record["authority"] and not record ["additional"]:
      print(f"No records found for '{domain}'. Domain may not exist")
      return None

    for k in record["answer"]:
      add_to_cache(str(k.rname),k.rtype, k.rdata)
      print("Answer:", k)
    for k in record["authority"]:
      add_to_cache(str(k.rname),k.rtype, k.rdata)
      print("Authority:", k)
    for k in record["additional"]:
      add_to_cache(str(k.rname),k.rtype, k.rdata)
      print("Additional:", k)
    
    if domain in cache and "A" in cache[domain]:
      print(f"")
      return cache[domain]["A"]
    
    if len(record["answer"]) > 0 and record["answer"][0].rtype == QTYPE.CNAME:
      cname = str(record["answer"][0].rdata)
      print(f"Alias detected: {domain} is an alias for {cname} ")
      domain = cname
      NS = ROOT_SERVER
      continue
    
    if record["authority"]:
      rs = str(record['authority'][0].rdata)
      print(f" Next server candiadate: {rs}")

      if rs in cache and "A" in cache[rs]:
          NS = cache[rs]["A"]
      else:
          NS = start_server(sock, rs, cache)
    else:
      print(" No authority information is available at this time!")


def manage_cache(cache:dict):
  if not cache:
    print("Cache is empty")
  else:
    print("Cache contents")
    for i, (key, value) in enumerate(cache.items(), start=1):
        print(f"{i}. {key}: {value}")

def remove_cache(l:int, cache:dict):
  if l <= 0 or l > len(cache):
    print("Invalid index")
    return
  key = list(cache.keys())[l-1]
  del cache[key]
  print(f"Removed {key}")
  
if __name__ == '__main__':
  # Create a UDP socket
  cache = dict()
  sock = socket(AF_INET, SOCK_DGRAM)
  sock.settimeout(2)

  while True:
    domain_name = input("Enter a domain name or .list/.clear/.remove N/.exit > ")
    
    if domain_name == '.exit':
      break

    elif domain_name == '.list':
      manage_cache(cache)
      continue

    elif domain_name == '.clear':
      cache.clear()
      print("Cache cleared")
      continue

    elif domain_name.startswith('.remove'):
      try:
          _, n = domain_name.split()
          remove_cache(int(n), cache)
      except Exception:
          print(" Usage: .remove N")
      continue



    
    start_server(sock, domain_name, cache)

  sock.close()

  
