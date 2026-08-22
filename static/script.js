const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const chatBox = document.getElementById("chatBox");
const newChatBtn = document.getElementById("newChatBtn");
const voiceBtn = document.getElementById("voiceBtn");
const searchInput = document.getElementById("searchInput");


// =========================================================
// CURRENT CONVERSATION
// =========================================================

let currentConversationId = null;


// =========================================================
// LOAD RECENT CONVERSATIONS
// =========================================================

async function loadRecentConversations() {

    try {

        const response = await fetch("/conversations");

        if (!response.ok) {
            throw new Error("Failed to load conversations");
        }

        const conversations = await response.json();

        const conversationList =
            document.getElementById("conversationList");

        if (!conversationList) {
            return;
        }

        conversationList.innerHTML = "";

        if (conversations.length === 0) {

            conversationList.innerHTML = `
                <div class="empty-conversations">
                    No recent conversations
                </div>
            `;

            return;
        }


        conversations.forEach(conversation => {

            const item = document.createElement("div");

            item.className = "conversation-item";

            /*
             * Your current Flask /conversations route
             * returns user_message, bot_response and timestamp.
             */

            item.innerHTML = `

                <div class="conversation-title">
                    ${escapeHtml(
                        conversation.user_message ||
                        "Conversation"
                    )}
                </div>
                <button
        class="delete-conversation"
        title="Delete conversation"
    >
        🗑️
    </button>

            `;
            const deleteButton =
    item.querySelector(".delete-conversation");

deleteButton.addEventListener(
    "click",
    async function(event) {

        event.stopPropagation();

        const confirmed = confirm(
            "Are you sure you want to delete this conversation?"
        );

        if (!confirmed) {
            return;
        }

        try {

            const response = await fetch(
                `/conversations/${conversation.id}`,
                {
                    method: "DELETE"
                }
            );

            const data =
                await response.json();

            if (!response.ok) {

                alert(
                    data.message ||
                    "Failed to delete conversation."
                );

                return;
            }

            // Remove from UI
            item.remove();

            // Reload list
            await loadRecentConversations();

        } catch (error) {

            console.error(
                "Delete error:",
                error
            );

            alert(
                "Something went wrong while deleting."
            );

        }

    }
);


            const title =
                item.querySelector(".conversation-title");

            title.addEventListener("click", function() {

                /*
                 * Your current Flask backend does not have
                 * /conversations/<id>.
                 *
                 * Therefore we don't try to open old
                 * conversations here.
                 */

                console.log(
                    "Conversation:",
                    conversation
                );

            });


            conversationList.appendChild(item);

        });


    } catch (error) {

        console.error(
            "Error loading recent conversations:",
            error
        );

    }

}


// =========================================================
// SEND MESSAGE
// =========================================================

async function sendMessage() {

    const question =
        questionInput.value.trim();


    // Don't send empty question
    if (!question) {
        return;
    }


    // =====================================================
    // SHOW USER MESSAGE
    // =====================================================

    chatBox.innerHTML += `

        <div class="user-message">
            ${escapeHtml(question)}
        </div>

    `;


    // Clear input
    questionInput.value = "";

    questionInput.style.height = "auto";


    chatBox.scrollTop =
        chatBox.scrollHeight;


    // =====================================================
    // LOADING MESSAGE
    // =====================================================

    const loadingMessage =
        document.createElement("div");

    loadingMessage.className =
        "assistant-message";

    loadingMessage.innerHTML =
        "🤖 Thinking...";

    chatBox.appendChild(
        loadingMessage
    );


    try {

        // =================================================
        // SEND QUESTION TO FLASK
        // =================================================

        const response =
            await fetch("/ask", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    /*
                     * IMPORTANT:
                     * Flask expects "message"
                     *
                     * Before you had:
                     *
                     * message: message
                     *
                     * but "message" variable did not exist.
                     */

                    message: question

                })

            });


        // =================================================
        // CHECK RESPONSE
        // =================================================

        const data =
            await response.json();


        if (!response.ok) {

            loadingMessage.remove();

            const errorMessage =
                data.error ||
                data.answer ||
                "Something went wrong.";

            chatBox.innerHTML += `

                <div class="assistant-message">
                    ❌ ${escapeHtml(errorMessage)}
                </div>

            `;

            return;
        }


        // =================================================
        // REMOVE LOADING
        // =================================================

        loadingMessage.remove();


        // =================================================
        // SHOW AI ANSWER
        // =================================================

        const answer =
            data.answer ||
            "I couldn't generate an answer.";


        chatBox.innerHTML += `

            <div class="assistant-message">

                ${escapeHtml(answer)
                    .replace(/\n/g, "<br>")}

            </div>

        `;


        chatBox.scrollTop =
            chatBox.scrollHeight;


        // =================================================
        // REFRESH RECENT CONVERSATIONS
        // =================================================

        await loadRecentConversations();


    } catch (error) {

        console.error(
            "Chat error:",
            error
        );


        loadingMessage.innerHTML =
            "❌ Something went wrong. Please try again.";

    }

}


// =========================================================
// NEW CHAT
// =========================================================

if (newChatBtn) {

    newChatBtn.addEventListener(
        "click",
        function() {

            currentConversationId = null;

            showWelcomeMessage();

            questionInput.value = "";

            questionInput.style.height = "auto";

            questionInput.focus();

        }
    );

}


// =========================================================
// WELCOME MESSAGE
// =========================================================

function showWelcomeMessage() {

    chatBox.innerHTML = `

        <div class="welcome-message">

            <h2>👋 Welcome</h2>

            <p>
                I am your AI Industrial Safety
                and Maintenance Assistant.
            </p>

            <p>
                Ask me about machine maintenance,
                safety procedures, vibration,
                overheating, bearings, and more.
            </p>

        </div>

    `;

}


// =========================================================
// SEND BUTTON
// =========================================================

if (sendBtn) {

    sendBtn.addEventListener(
        "click",
        sendMessage
    );

}


// =========================================================
// ENTER KEY
// =========================================================

if (questionInput) {

    questionInput.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter" && !event.shiftKey) {

                event.preventDefault();

                sendMessage();

            }

        }
    );

}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text == null ? "" : String(text);

    return div.innerHTML;

}


// =========================================================
// LOAD WHEN PAGE OPENS
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadRecentConversations();

    }
);


// =========================================================
// SEARCH CONVERSATIONS
// =========================================================

if (searchInput) {

    searchInput.addEventListener(
        "input",
        function() {

            const searchText =
                searchInput.value
                    .toLowerCase()
                    .trim();

            const conversations =
                document.querySelectorAll(
                    ".conversation-item"
                );


            conversations.forEach(item => {

                const title =
                    item.querySelector(
                        ".conversation-title"
                    );

                if (!title) {
                    return;
                }


                const conversationTitle =
                    title.textContent
                        .toLowerCase();


                if (
                    conversationTitle
                        .includes(searchText)
                ) {

                    item.style.display =
                        "flex";

                } else {

                    item.style.display =
                        "none";

                }

            });

        }
    );

}


// =========================================================
// VOICE INPUT
// =========================================================

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


if (
    SpeechRecognition &&
    voiceBtn
) {

    const recognition =
        new SpeechRecognition();


    recognition.continuous = false;

    recognition.interimResults = false;

    recognition.lang = "en-IN";


    voiceBtn.addEventListener(
        "click",
        function() {

            try {

                recognition.start();

                voiceBtn.innerHTML = "🔴";

                voiceBtn.title =
                    "Listening...";

            } catch (error) {

                console.log(
                    "Voice already running"
                );

            }

        }
    );


    recognition.onresult =
        function(event) {

            const transcript =
                event.results[0][0]
                    .transcript;


            questionInput.value =
                transcript;

        };


    recognition.onend =
        function() {

            voiceBtn.innerHTML =
                "🎙️";

            voiceBtn.title =
                "Voice input";

        };


    recognition.onerror =
        function(event) {

            console.error(
                "Voice recognition error:",
                event.error
            );


            voiceBtn.innerHTML =
                "🎙️";

            voiceBtn.title =
                "Voice input";

        };

} else if (voiceBtn) {

    voiceBtn.disabled = true;

    console.log(
        "Speech recognition is not supported in this browser."
    );

}


// =========================================================
// AUTO RESIZE TEXTAREA
// =========================================================

if (questionInput) {

    questionInput.addEventListener(
        "input",
        function() {

            this.style.height = "auto";

            this.style.height =
                Math.min(
                    this.scrollHeight,
                    150
                ) + "px";

        }
    );

}