# YubiKey signing when working with an AI agent

## Diagnosis on this workstation

Git has `commit.gpgsign=true` and `user.signingkey` points to
`~/.ssh/id_ecdsa_sk.pub`, but `gpg.format` is unset. Git therefore invoked
OpenPGP/GPG with an SSH key path, producing "No secret key". This does not show
that the hardware key is broken. The Windows SSH-agent connection also failed
during the read-only check.

No signing configuration or key material was changed.

## Recommended workflow

Let the agent edit, test, and prepare a focused staged diff. Review it, then sign
one meaningful commit with the YubiKey. Sign the release tag when ready.
Grouping work avoids repeated hardware prompts without weakening the key policy.

For this SSH key, the relevant repository-local configuration is:

```powershell
git config --local gpg.format ssh
git config --local user.signingkey "$env:USERPROFILE\.ssh\id_ecdsa_sk.pub"
git config --local gpg.ssh.program "C:/Windows/System32/OpenSSH/ssh-keygen.exe"
git config --local commit.gpgsign true
```

These are suggested commands for the user to review and run, not changes made by
the agent. Confirm that this OpenSSH build supports your FIDO key. Add the public
key to GitHub as a **signing** key if it is currently registered only for authentication.

If using Windows ssh-agent, start its service and load the existing key handle:

```powershell
# Service setup may require an Administrator PowerShell.
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add "$env:USERPROFILE\.ssh\id_ecdsa_sk"
```

The agent can remember the key handle; hardware presence/PIN requirements remain.
Enter PINs only in the local trusted prompt, never in the conversation.

## If fully unattended commits are required

Use a distinct automation identity and software signing key or GitHub App for
agent branches, with access restricted to the necessary repositories. Keep review
and final integration under your identity and YubiKey. This changes the trust
model, so choose it deliberately rather than disabling signing globally.

Sources: [GitHub SSH signing configuration](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key)
and [Yubico FIDO2/OpenSSH guidance](https://developers.yubico.com/SSH/Securing_SSH_with_FIDO2.html).