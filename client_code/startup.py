"""The app starts here (anvil.yaml: startup module). One server call to learn who is signed in (Anvil's loading
spinner shows meanwhile), the Privacy & Terms kit, then the page for the address in the browser bar."""
import json

import anvil.server
from anvil.js import window

from . import legal, router, state

LEGAL_THEME = {"accent": "#C2255C"}  # colours for the Privacy & Terms page (match --c-brand in app.css)


def _test_call(name, args_json):
    """Test hook for tools/ui/*.js: the same server call any page makes, as JSON text (window.phCall)."""
    return json.dumps(anvil.server.call(name, *json.loads(args_json)))


window.phCall = _test_call
legal.setup(LEGAL_THEME)
state.set_me(anvil.server.call("get_me"))
if state.me():
    legal.refresh_soon()
router.start()
