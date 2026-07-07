(function () {
  var script = document.currentScript;
  if (!script) {
    return;
  }

  var apiKey = script.getAttribute("data-api-key");
  var chatUrl = script.getAttribute("data-chat-url");

  if (!apiKey || !chatUrl) {
    return;
  }

  var style = document.createElement("style");
  style.textContent = ""
    + ".ragbot-widget{position:fixed;right:20px;bottom:20px;z-index:9999;font-family:Arial,sans-serif;}"
    + ".ragbot-toggle{background:#111827;color:#fff;border:none;border-radius:999px;padding:12px 16px;cursor:pointer;font-size:14px;}"
    + ".ragbot-panel{display:none;width:320px;height:420px;background:#fff;border:1px solid #d1d5db;border-radius:8px;box-shadow:0 10px 30px rgba(0,0,0,0.15);overflow:hidden;}"
    + ".ragbot-panel.open{display:flex;flex-direction:column;}"
    + ".ragbot-header{padding:12px 14px;background:#111827;color:#fff;font-size:14px;}"
    + ".ragbot-messages{flex:1;padding:12px;overflow-y:auto;background:#f9fafb;display:flex;flex-direction:column;gap:8px;}"
    + ".ragbot-message{padding:10px 12px;border-radius:8px;max-width:85%;font-size:14px;line-height:1.4;white-space:pre-wrap;}"
    + ".ragbot-message.user{background:#111827;color:#fff;align-self:flex-end;}"
    + ".ragbot-message.bot{background:#e5e7eb;color:#111827;align-self:flex-start;}"
    + ".ragbot-form{display:flex;gap:8px;padding:12px;border-top:1px solid #e5e7eb;background:#fff;}"
    + ".ragbot-input{flex:1;padding:10px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;}"
    + ".ragbot-send{background:#2563eb;color:#fff;border:none;border-radius:6px;padding:10px 12px;cursor:pointer;font-size:14px;}"
    + ".ragbot-send:disabled{opacity:0.6;cursor:default;}";
  document.head.appendChild(style);

  var root = document.createElement("div");
  root.className = "ragbot-widget";
  root.innerHTML = ""
    + '<div class="ragbot-panel">'
    + '  <div class="ragbot-header">Chat with us</div>'
    + '  <div class="ragbot-messages"></div>'
    + '  <form class="ragbot-form">'
    + '    <input class="ragbot-input" type="text" placeholder="Ask a question..." />'
    + '    <button class="ragbot-send" type="submit">Send</button>'
    + "  </form>"
    + "</div>"
    + '<button class="ragbot-toggle" type="button">Chat</button>';
  document.body.appendChild(root);

  var panel = root.querySelector(".ragbot-panel");
  var toggle = root.querySelector(".ragbot-toggle");
  var form = root.querySelector(".ragbot-form");
  var input = root.querySelector(".ragbot-input");
  var sendButton = root.querySelector(".ragbot-send");
  var messages = root.querySelector(".ragbot-messages");

  function addMessage(text, type) {
    var item = document.createElement("div");
    item.className = "ragbot-message " + type;
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendQuestion(question) {
    sendButton.disabled = true;

    try {
      var body = new URLSearchParams();
      body.append("question", question);
      body.append("api_key", apiKey);

      var response = await fetch(chatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: body.toString()
      });

      var data = await response.json();

      if (!response.ok) {
        addMessage(data.detail || "Something went wrong.", "bot");
        return;
      }

      addMessage(data.answer || "No answer found.", "bot");
    } catch (error) {
      addMessage("Unable to reach the chat server.", "bot");
    } finally {
      sendButton.disabled = false;
    }
  }

  toggle.addEventListener("click", function () {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) {
      input.focus();
    }
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    var question = input.value.trim();
    if (!question) {
      return;
    }

    addMessage(question, "user");
    input.value = "";
    sendQuestion(question);
  });
})();
