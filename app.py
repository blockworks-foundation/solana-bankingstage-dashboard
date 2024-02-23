from http.client import HTTPException

from flask import Flask, render_template, request, make_response, redirect
from flask_htmx import HTMX
import time
import re
import transaction_database
import transaction_details_database
import recent_blocks_database
import block_details_database
import config
import locale
from datetime import datetime
import account_details_database

#
# MAIN
#

print("Setting up Flask webapp...")
webapp = Flask(__name__)
htmx = HTMX(webapp)


print("SOLANA_CLUSTER", config.get_config()['cluster'])
print("LOCALE", locale.getlocale())
# transaction_database.run_query()
# recent_blocks_database.run_query()
# block_details_database.find_block_by_slotnumber(226352855)
# print("SELFTEST passed")


@webapp.route('/')
def index():
    return redirect("/tx-errors", code=302)


# fly.io service health check
@webapp.route('/health')
def health():
    return "UP\r\n", 200


@webapp.route('/dashboard')
def dashboard():
    return redirect("/tx-errors", code=302)


@webapp.route('/tx-errors')
def tx_errors():
    this_config = config.get_config()
    rows_limit = request.args.get('limit', default = 50, type = int)
    assert rows_limit > 0, "limit must be positive"
    assert rows_limit <= 10000, "max limit is 10000"

    start = time.time()
    maprows = list(transaction_database.run_query(transaction_row_limit=rows_limit))
    elapsed = time.time() - start
    if elapsed > .5:
        print("transaction_database.RunQuery() took", elapsed, "seconds")
    return render_template('tx-errors.html', config=this_config, transactions=maprows)


@webapp.route('/recent-blocks')
def recent_blocks():
    this_config = config.get_config()
    to_slot = request.args.get('to_slot', default = 0, type = int)
    if to_slot == 0:
        to_slot = None

    start = time.time()
    maprows = list(recent_blocks_database.run_query(to_slot, blocks_row_limit=100))
    elapsed = time.time() - start
    if elapsed > .5:
        print("recent_blocks_database.RunQuery() took", elapsed, "seconds")

    enable_polling = "true" if to_slot is None else "false"

    return render_template('recent_blocks.html', config=this_config, blocks=maprows, enable_polling=enable_polling)


@webapp.route('/block/<path:slot>')
def get_block(slot):
    this_config = config.get_config()
    start = time.time()
    block = block_details_database.find_block_by_slotnumber(slot)
    elapsed = time.time() - start
    if elapsed > .5:
        print("block_details_database.find_block_by_slotnumber() took", elapsed, "seconds")
    return render_template('block_details.html', config=this_config, block=block)


@webapp.route('/account/<path:pubkey>')
def get_account(pubkey):
    this_config = config.get_config()
    start = time.time()
    if not is_b58_44(pubkey):
        return "Invalid account", 404
    start = time.time()
    (account, blocks, transactions) = account_details_database.build_account_details(pubkey, recent_blocks_row_limit=10, transaction_row_limit=100)
    elapsed = time.time() - start
    if elapsed > .5:
        print("account_details_database.build_account_details() took", elapsed, "seconds")
    return render_template('account_details.html', config=this_config, account=account, recent_blocks=blocks, transactions=transactions)


def is_slot_number(raw_string):
    return re.fullmatch("[0-9,]+", raw_string) is not None


# used for blockhash AND account pubkey
def is_b58_44(raw_string):
    return re.fullmatch("[0-9a-zA-Z]{43,44}", raw_string) is not None


def is_tx_sig(raw_string):
    # regex is not perfect - feel free to improve
    if is_b58_44(raw_string):
        return False
    return re.fullmatch("[0-9a-zA-Z]{86,88}", raw_string) is not None


# account address
# if NOT blockhash
def is_account_key(raw_string):
    return re.fullmatch("[0-9a-zA-Z]{32,44}", raw_string) is not None


@webapp.route('/search', methods=["GET"])
def search_page():
    this_config = config.get_config()
    return render_template('search.html', config=this_config)


@webapp.route('/search/<path:searchstring>', methods=["GET"])
def search_deeplink(searchstring):
    this_config = config.get_config()
    return render_template('search.html', config=this_config, search_string=searchstring)


# please prefix all database methods with "search_" and use them only for search
@webapp.route('/search', methods=["POST"])
def search_form():
    assert htmx, "htmx must be enabled"
    search_string = request.form.get("search").strip()
    return search_and_render(search_string)


def search_and_render(search_string):
    this_config = config.get_config()

    if search_string == "":
        return render_template('_search_noresult.html', config=this_config)

    if is_slot_number(search_string):
        search_string = search_string.replace(',', '')
        maprows = list(recent_blocks_database.search_block_by_slotnumber(int(search_string)))
        if len(maprows):
            # match
            return (
                render_template('_blockslist.html', config=this_config, blocks=maprows),
                make_search_deeplink_header(search_string)
            )
        else:
            return render_template('_search_noresult.html', config=this_config)

    is_blockhash = block_details_database.is_matching_blockhash(search_string)

    if is_blockhash:
        print("blockhash search=", search_string)
        maprows = list(recent_blocks_database.search_block_by_blockhash(search_string))
        if len(maprows):
            # match
            return (
                render_template('_blockslist.html', config=this_config, blocks=maprows),
                make_search_deeplink_header(search_string)
            )
        else:
            return render_template('_search_noresult.html', config=this_config)
    elif not is_blockhash and is_b58_44(search_string):
        print("account address search=", search_string)
        maprows_account = account_details_database.search_account_by_key(search_string)
        if len(maprows_account) != 1:
            return render_template('_search_noresult.html', config=this_config)
        account = maprows_account[0]

        (maprows, is_limit_exceeded) = list(transaction_database.search_transactions_by_address(search_string))
        if len(maprows):
            # match
            return (
                render_template('_search_accountresult.html', config=this_config, account=account, transactions=maprows, limit_exceeded=is_limit_exceeded),
                make_search_deeplink_header(search_string)
            )
        else:
            return render_template('_search_noresult.html', config=this_config)
    elif is_tx_sig(search_string):
        print("txsig search=", search_string)
        maprows = list(transaction_database.search_transaction_by_sig(search_string))
        if len(maprows):
            # match
            return (
                render_template('_txlist.html', config=this_config, transactions=maprows, limit_exceeded=False),
                make_search_deeplink_header(search_string)
            )
        else:
            return render_template('_search_noresult.html', config=this_config)
    else:
        return render_template('_search_unsupported.html', config=this_config, search_string=search_string)


def make_search_deeplink_header(search_string):
    return {'HX-Replace-Url': '/search/' + search_string}


@webapp.route('/transaction/<path:signature>')
def get_transaction_details(signature):
    this_config = config.get_config()
    start = time.time()
    maprows = list(transaction_details_database.find_transaction_details_by_sig(signature))
    elapsed = time.time() - start
    if elapsed > .5:
        print("transaction_database.find_transaction_details_by_sig() took", elapsed, "seconds")
    if len(maprows):
        return render_template('transaction_details.html', config=this_config, transaction=maprows[0])
    else:
        return render_not_found(object_type="Transaction", object_id=signature)


# format 123456789 to "123,456,789"
@webapp.template_filter('lamports')
def lamports_filter(number: int):
    if number is None:
        return ""
    else:
        try:
            return format(number, ",")
        except TypeError:
            print("FIELD_ERROR in template filter")
            return "FIELD_ERROR"


@webapp.template_filter('slotnumber')
def slotnumber_filter(number: int):
    if number is None:
        return ""
    else:
        try:
            return format(number, ",")
        except TypeError:
            print("FIELD_ERROR in template filter")
            return "FIELD_ERROR"


@webapp.template_filter('count')
def count_filter(number: int):
    if number is None:
        return ""
    else:
        try:
            return format(number, ",")
        except TypeError:
            print("FIELD_ERROR in template filter")
            return "FIELD_ERROR"


# railway version: None -> None
@webapp.template_filter('map_count')
def mapcount_filter(number: int):
    if number is None:
        return None
    else:
        try:
            return format(number, ",")
        except TypeError:
            print("FIELD_ERROR in template filter")
            return "FIELD_ERROR"


@webapp.template_filter('timestamp')
def timestamp_filter(dt: datetime):
    if dt is None:
        return None
    else:
        try:
            return dt.strftime('%a %d %b %H:%M:%SZ')
        except TypeError:
            print("FIELD_ERROR in template filter")
            return "FIELD_ERROR"


def render_not_found(object_type, object_id):
    this_config = config.get_config()
    return render_template("404_errorpage.html", config=this_config, object_type=object_type, object_id=object_id), 404


@webapp.errorhandler(404)
def resource_not_found(e):
    print("ERROR 404 (will show 404_errorpage.html)", request.url)
    return render_not_found(object_type="URL", object_id=request.url)


@webapp.errorhandler(Exception)
def handle_exception(e):
    this_config = config.get_config()

    if e.__cause__ is not None:
        errortext = "{exception} ({cause})".format(exception = e, cause = e.__cause__)
    else:
        errortext = "{exception}".format(exception = e)

    print("APPLICATION ERROR (will show 500_errorpage.html): ", errortext)
    return render_template("500_errorpage.html", exception=errortext, config=this_config), 500
