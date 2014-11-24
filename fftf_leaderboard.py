import hashlib
import json
import grequests
import string

class FFTFLeaderboard():

    debug_mode = False
    pool_size = 1
    api_key = None

    def __init__(self, debug_mode, pool_size, api_key):

        self.debug_mode = debug_mode
        self.pool_size = pool_size
        self.api_key = api_key

    def log_call(self, params, campaign, request):

        if params['fftfCampaign'] == None or params['fftfReferer'] == None:
            return

        i = int(request.values.get('call_index'))

        kwds = {
            'campaign_id': campaign['id'],
            'member_id': params['repIds'][i],
            'zipcode': params['zipcode'],
            'phone_number': hashlib.sha256(params['userPhone']).hexdigest(),
            'call_id': request.values.get('CallSid', None),
            'status': request.values.get('DialCallStatus', 'unknown'),
            'duration': request.values.get('DialCallDuration', 0)
        }
        data = json.dumps(kwds)

        self.post_to_leaderboard(
            params['fftfCampaign'],
            'call',
            data,
            params['fftfReferer'],
            params['fftfSession'])

    def log_complete(self, params, campaign, request):

        if params['fftfCampaign'] == None or params['fftfReferer'] == None:
            return

        self.post_to_leaderboard(
            params['fftfCampaign'],
            'calls_complete',
            'yay',
            params['fftfReferer'],
            params['fftfSession'])

    def post_to_leaderboard(self, fftf_campaign, stat, data, host, session):

        debug_mode = self.debug_mode

        def finished(res, **kwargs):
            if debug_mode:
                print "FFTF Leaderboard call complete: %s" % res

        data = {
            'campaign': fftf_campaign,
            'stat': stat,
            'data': data,
            'host': host,
            'session': session
        }

        if self.debug_mode:
            print "FFTF Leaderboard sending: %s" % data

        url = 'https://leaderboard.fightforthefuture.org/log'
        req = grequests.post(url, data=data, hooks=dict(response=finished))
        job = grequests.send(req, grequests.Pool(self.pool_size))

        return

    def log_extra_data(self, params, campaign, request, to_phone, call_index):

        debug_mode = self.debug_mode

        def finished(res, **kwargs):
            if debug_mode:
                print "FFTF Extra Data log call complete: %s" % res

        ip = hashlib.sha256(request.values.get("ip_address", "")).hexdigest()

        data = {
            'key': self.api_key,
            'campaign_id': campaign['id'],
            'from_phone_number': string.replace(params['userPhone'], "-", ""),
            'to_phone_number': string.replace(to_phone, "-", ""),
            'ip_address': ip,
            'call_index': call_index
        }

        if self.debug_mode:
            print "FFTF Log Extra Data sending: %s" % data

        url = 'https://queue.fightforthefuture.org/log_phone_call'
        req = grequests.post(url, data=data, hooks=dict(response=finished))
        job = grequests.send(req, grequests.Pool(self.pool_size))

        return