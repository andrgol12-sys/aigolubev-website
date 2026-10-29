document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("faq-toggle");
    const panel = document.getElementById("faq-panel");
    const close = document.getElementById("faq-close");
    const form = document.getElementById("faq-form");
    const input = document.getElementById("faq-input");
    const messages = document.getElementById("faq-messages");
    const send = document.getElementById("faq-send");

    if (!toggle || !panel || !close || !form || !input || !messages || !send) {
        return;
    }

    function setOpen(isOpen) {
        panel.hidden = !isOpen;
        toggle.setAttribute("aria-expanded", String(isOpen));

        if (isOpen) {
            input.focus();
        } else {
            toggle.focus();
        }
    }

    toggle.addEventListener("click", () => {
        setOpen(panel.hidden);
    });

    close.addEventListener("click", () => {
        setOpen(false);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !panel.hidden) {
            setOpen(false);
        }
    });

    function addMessage(text, type) {
        const element = document.createElement("div");
        element.className = `faq-message faq-message-${type}`;

        // textContent исключает выполнение HTML из ответа модели.
        element.textContent = text;

        messages.appendChild(element);
        messages.scrollTop = messages.scrollHeight;

        return element;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const question = input.value.trim();

        if (!question || question.length > 1000) {
            return;
        }

        addMessage(question, "user");

        input.value = "";
        input.disabled = true;
        send.disabled = true;

        const waiting = addMessage("Подготавливаю ответ...", "bot");

        try {
            const response = await fetch("/api/faq/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector(
                        'meta[name="faq-csrf-token"]'
                    ).content,
                },
                credentials: "same-origin",
                body: JSON.stringify({ question }),
            });

            const data = await response.json();

            if (!response.ok) {
                waiting.textContent =
                    data.error || data.message ||
                    "Не удалось обработать вопрос. Попробуйте позже.";
                return;
            }

            waiting.textContent =
                data.answer || data.message ||
                "Не удалось получить ответ.";
        } catch (error) {
            waiting.textContent =
                "Ошибка соединения. Попробуйте отправить вопрос позже.";
        } finally {
            input.disabled = false;
            send.disabled = false;

            if (!panel.hidden) {
                input.focus();
            }

            messages.scrollTop = messages.scrollHeight;
        }
    });
});