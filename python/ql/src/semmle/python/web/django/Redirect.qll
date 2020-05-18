/**
 * Provides class representing the `django.redirect` function.
 * This module is intended to be imported into a taint-tracking query
 * to extend `TaintSink`.
 */

import python
import semmle.python.security.TaintTracking
import semmle.python.security.strings.Basic
private import semmle.python.web.django.Shared
private import semmle.python.web.Http

/**
 * The URL argument for a call to the `django.shortcuts.redirect` function.
 */
class DjangoShortcutsRedirectSink extends HttpRedirectTaintSink {
    override string toString() { result = "DjangoShortcutsRedirectSink" }

    DjangoShortcutsRedirectSink() {
        this = Value::named("django.shortcuts.redirect").(FunctionValue).getArgumentForCall(_, 0)
    }
}

/**
 * The URL argument when instantiating a Django Redirect Response.
 */
class DjangoRedirectResponseSink extends HttpRedirectTaintSink {
    DjangoRedirectResponseSink() {
        exists(CallNode call |
            call = any(DjangoRedirectResponse rr).getACall()
        |
            this = call.getArg(0)
            or
            this = call.getArgByName("redirect_to")
        )
    }

    override string toString() { result = "DjangoRedirectResponseSink" }
}
