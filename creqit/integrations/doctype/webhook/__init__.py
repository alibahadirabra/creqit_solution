# Copyright (c) 2017, creqit Technologies and contributors
# License: MIT. See LICENSE

import creqit

supported_events = {
	"after_insert",
	"on_update",
	"on_submit",
	"on_cancel",
	"on_trash",
	"on_update_after_submit",
	"on_change",
}


def get_all_webhooks():
	# query webhooks
	webhooks_list = creqit.get_all(
		"Webhook",
		fields=["name", "condition", "webhook_docevent", "webhook_doctype", "background_jobs_queue"],
		filters={"enabled": True},
	)

	# make webhooks map
	webhooks = {}
	for w in webhooks_list:
		webhooks.setdefault(w.webhook_doctype, []).append(w)

	return webhooks


def run_webhooks(doc, method):
	"""Run webhooks for this method"""
	if method not in supported_events:
		return

	creqit_flags = creqit.local.flags

	if creqit_flags.in_import or creqit_flags.in_patch or creqit_flags.in_install or creqit_flags.in_migrate:
		return

	# load all webhooks from cache / DB
	webhooks = creqit.cache.get_value("webhooks", get_all_webhooks)

	# get webhooks for this doctype
	webhooks_for_doc = webhooks.get(doc.doctype, None)

	if not webhooks_for_doc:
		# no webhooks, quit
		return

	event_list = ["on_update", "after_insert", "on_submit", "on_cancel", "on_trash"]

	if not doc.flags.in_insert:
		# value change is not applicable in insert
		event_list.append("on_change")
		event_list.append("before_update_after_submit")

	from creqit.integrations.doctype.webhook.webhook import get_context

	for webhook in webhooks_for_doc:
		trigger_webhook = False
		event = method if method in event_list else None
		if not webhook.condition:
			trigger_webhook = True
		elif creqit.safe_eval(webhook.condition, eval_locals=get_context(doc)):
			trigger_webhook = True

		if trigger_webhook and event and webhook.webhook_docevent == event:
			_add_webhook_to_queue(webhook, doc)


def _add_webhook_to_queue(webhook, doc):
	# Maintain a queue and flush on commit
	if not getattr(creqit.local, "_webhook_queue", None):
		creqit.local._webhook_queue = []
		creqit.db.after_commit.add(flush_webhook_execution_queue)

	creqit.local._webhook_queue.append(creqit._dict(doc=doc, webhook=webhook))


def flush_webhook_execution_queue():
	"""Enqueue all pending webhook executions.

	Each webhook can trigger multiple times on same document or even different instance of same
	document. We assume that last enqueued version of document is the final document for this DB
	transaction.
	"""
	if not getattr(creqit.local, "_webhook_queue", None):
		return

	uniq_hooks = set()
	unique_last_instances = []

	# reverse
	creqit.local._webhook_queue.reverse()

	# deduplicate on (doc.name, webhook.name)
	# 'doc' holds the last instance values
	for execution in creqit.local._webhook_queue:
		key = (execution.webhook.get("name"), execution.doc.get("name"))
		if key not in uniq_hooks:
			uniq_hooks.add(key)
			unique_last_instances.append(execution)

	# Clear original queue so next enqueue computation happens correctly.
	del creqit.local._webhook_queue

	# reverse again, to get back the original order on which to execute webhooks
	unique_last_instances.reverse()

	for instance in unique_last_instances:
		creqit.enqueue(
			"creqit.integrations.doctype.webhook.webhook.enqueue_webhook",
			doc=instance.doc,
			webhook=instance.webhook,
			now=creqit.flags.in_test,
			queue=instance.webhook.background_jobs_queue or "default",
		)
