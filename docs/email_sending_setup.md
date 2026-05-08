# Resend / Email Sending Setup

Operational sender for the first Industry Mood outreach wave:

```text
Industry Mood <admin@industrymood.com>
```

## 1. Create local .env

Copy the template:

```bash
cp .env.example .env
```

Fill:

```bash
RESEND_API_KEY=your_resend_api_key
OUTREACH_FROM_EMAIL="Industry Mood <admin@industrymood.com>"
```

Do not commit `.env`.

## 2. Verify domain in Resend

In Resend:

1. Add `industrymood.com` as the sending domain.
2. Copy the DNS records Resend gives you.
3. Add those records in the DNS provider.
4. Wait until Resend marks the domain as verified.

Current observed DNS for `industrymood.com`:

```text
MX:
  0 smtp.secureserver.net.
  10 mailstore1.secureserver.net.

SPF:
  v=spf1 include:secureserver.net -all

DMARC:
  v=DMARC1; p=quarantine; adkim=r; aspf=r; rua=mailto:dmarc_rua@onsecureserver.net;
```

Important: do not delete the existing MX records unless you are intentionally moving the mailbox provider. Resend sending verification should not break the mailbox used by `admin@industrymood.com`.

## 3. Safer alternative: dedicated subdomain

If Resend verification or deliverability becomes risky on the root domain, use a subdomain instead:

```text
Industry Mood <admin@outreach.industrymood.com>
```

or:

```text
Industry Mood <admin@mail.industrymood.com>
```

This keeps the main operational mailbox separate from cold outreach reputation.

## 4. Test with dry-run first

Generate and approve drafts, then run:

```bash
python send_drafts.py --db drafts_queue.db --mode dry-run --limit 5
```

Confirm the exact subjects and body copy before real sending.

## 5. Real send command

Only after Resend domain verification succeeds:

```bash
python send_drafts.py --db drafts_queue.db --mode resend --limit 5 --confirm-real-send
```

Guardrails:

- `--limit 5` caps successful sends for the run.
- `--confirm-real-send` is required for Resend to prevent accidental real outreach.
- Invalid email syntax is suppressed before sending.
- Suppressed/replied/bounced contacts are skipped.

## 6. First-wave operating rule

Start with 5-10 manually approved emails per day. Do not send the full 66-contact first wave at once.

After each sending batch:

```bash
python report.py --db drafts_queue.db
```

Track:

- replies,
- positive replies,
- demos booked,
- not interested,
- bounces.
