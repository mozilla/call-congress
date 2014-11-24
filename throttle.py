import os, psycopg2, hashlib

class Throttle():

    conn = None

    def __init__(self):

        db   = os.environ.get('MOTHERSHIP_POSTGRES_DB')
        user = os.environ.get('MOTHERSHIP_POSTGRES_USER')
        pswd = os.environ.get('MOTHERSHIP_POSTGRES_PASS')
        host = os.environ.get('MOTHERSHIP_POSTGRES_HOST')
        port = os.environ.get('MOTHERSHIP_POSTGRES_PORT')
        self.conn = psycopg2.connect(database=db, user=user, password=pswd,
            host=host, port=port)

    def throttle(self, campaign_id, from_phone_number, ip_address, override):
        """Records call info in the log"""

        if from_phone_number == '' or len(from_phone_number) != 10:
            print "THROTTLE TRIP! --- Bad from_phone_number!"

        from_phone_number = format_phone_number(from_phone_number)

        conn = self.conn
        cur = conn.cursor()

        flag_number = 0
        flag_ip = 0
        is_whitelisted = 0

        hashed_ip_address = hashlib.sha256(ip_address).hexdigest()

        qry = ("SELECT count(id) FROM _ms_call_throttle WHERE "
               "create_date >= NOW() - '1 day'::INTERVAL "
               " AND campaign_id=%s AND from_phone_number=%s")
        cur.execute(qry, (campaign_id, from_phone_number))
        recent_from_phone_number = cur.fetchone()

        if recent_from_phone_number[0] > 1:
            flag_number = 1

        qry = ("SELECT count(id) FROM _ms_call_throttle WHERE "
               "create_date >= NOW() - '1 day'::INTERVAL "
               " AND campaign_id=%s AND (ip_address=%s OR ip_address=%s)")
        cur.execute(qry, (campaign_id, ip_address, hashed_ip_address))
        recent_ip_address = cur.fetchone()

        if recent_ip_address[0] > 1:
            flag_ip = 1

        if override == os.environ.get('THROTTLE_OVERRIDE_KEY'):
            flag_ip = 0
            flag_number = 0
            is_whitelisted = 1

        if flag_number == 0 and flag_ip == 0:
            ip_address = hashed_ip_address

        cur.execute(("INSERT INTO _ms_call_throttle "
                     "      (campaign_id, from_phone_number, is_whitelisted, "
                     "          ip_address, flag_number, flag_ip, create_date) "
                     "VALUES "
                     "      (%s, %s, %s, %s, %s, %s, NOW())"),
                    (campaign_id, from_phone_number, is_whitelisted, ip_address,
                        flag_number, flag_ip))

        conn.commit()
        cur.close()

        if flag_number:
            print "THROTTLE TRIP! --- from_phone_number %s / %s" % \
                (from_phone_number, recent_from_phone_number[0])
            return True
        elif flag_ip:
            print "THROTTLE TRIP! --- ip_address %s / %s" % \
                (ip_address, recent_ip_address[0])
            return True

        return False

def format_phone_number(phone_number):
    return phone_number[:3] + "-" + phone_number[3:6] + "-" + phone_number[6:10]