// Envia o e-mail do cadastro para a rota /registrar-email (JSON).
// Espera ser chamado por um input + botão existentes na sua página.
// Uso típico (no HTML):
//   import './scripts/salvar_email.js' (ou incluir via <script type="module">)
//   e chamar `window.salvarEmailAparcima()`.

window.salvarEmailAparcima = async function salvarEmailAparcima(email) {
  try {
    const resposta = await fetch('/registrar-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    const dados = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
      const msg = dados?.erro || 'Falha ao salvar e-mail.';
      window.dispatchEvent(new CustomEvent('email-salvo:erro', { detail: { msg }}));
      return { ok: false, erro: msg };
    }

    window.dispatchEvent(new CustomEvent('email-salvo:ok', { detail: { msg: 'E-mail salvo com sucesso!' } }));
    return { ok: true };
  } catch (e) {
    const msg = e?.message || 'Erro inesperado ao salvar e-mail.';
    window.dispatchEvent(new CustomEvent('email-salvo:erro', { detail: { msg } }));
    return { ok: false, erro: msg };
  }
};

// Compat: se a página tiver um formulário com id="form-email" e input id="email-email",
// anexamos listener automaticamente.
(function attachIfPossible() {
  try {
    const form = document.getElementById('form-email');
    const input = document.getElementById('email-email');
    if (!form || !input) return;

    const msgEl = document.getElementById('email-message');

    const render = (msg, type) => {
      if (!msgEl) return;
      msgEl.textContent = msg;
      msgEl.style.color = type === 'error' ? '#ffb3b3' : '#d6ffe9';
      msgEl.style.fontWeight = '900';
    };

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      render('Salvando...', 'ok');

      const email = (input.value || '').trim();
      const r = await window.salvarEmailAparcima(email);
      if (r.ok) render('E-mail salvo com sucesso!', 'ok');
      else render(r.erro || 'Falha ao salvar e-mail.', 'error');
    });
  } catch {
    // ignore
  }
})();

