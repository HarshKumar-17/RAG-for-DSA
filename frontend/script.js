const chatBox = document.getElementById("chat-box");
const sendBtn = document.getElementById("send-btn");
const input = document.getElementById("user-input");
const newChatBtn = document.querySelector(".new-chat");

// Auto-resize textarea
input.addEventListener("input", function() {
    this.style.height = "48px";
    if (this.scrollHeight > 48) {
        this.style.height = Math.min(this.scrollHeight, 150) + "px";
    }
});

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keydown", function(e){
    if(e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        sendMessage();
    }
});

newChatBtn.addEventListener("click", newChat);

function addMessage(text, sender){
    const message = document.createElement("div");
    message.classList.add("message", sender);
    
    // Convert newlines to breaks for proper rendering
    message.innerHTML = text.replace(/\n/g, '<br>');
    
    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showTyping(){
    const typing = document.createElement("div");
    typing.classList.add("message", "bot", "typing");
    typing.id = "typing";
    
    typing.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;
    
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTyping(){
    const typing = document.getElementById("typing");
    if(typing) typing.remove();
}

async function sendMessage(){
    const message = input.value.trim();
    if(!message) return;
    
    addMessage(message, "user");
    input.value = "";
    input.style.height = "48px";
    
    showTyping();
    
    try {
        const response = await fetch("/chat",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({message:message})
        });
        
        removeTyping();

        let data;
        const text = await response.text();
        try {
            data = JSON.parse(text);
        } catch(e) {
            data = null;
        }

        if (!response.ok) {
            const errDetail = (data && data.response) ? data.response : (text.slice(0, 150) || `HTTP error ${response.status}`);
            addMessage(`⚠️ ${errDetail}`, "bot");
        } else if (data && data.response) {
            addMessage(data.response, "bot");
        } else {
            addMessage(text || "No response received.", "bot");
        }
    } catch(err) {
        removeTyping();
        addMessage(`⚠️ Connection error: ${err.message || "Failed to reach server"}`, "bot");
    }
}

function newChat(){
    chatBox.innerHTML = "";
    fetch("/reset", {
        method: "POST"
    });
}

async function loadHistory(){
    try {
        const response = await fetch("/history");
        const data = await response.json();
        const history = data.history;
        
        chatBox.innerHTML = "";
        
        history.forEach(msg => {
            if(msg.role === "user"){
                addMessage(msg.content, "user");
            } else {
                addMessage(msg.content, "bot");
            }
        });
    } catch (e) {
        console.log("No history or server offline");
    }
}

window.onload = loadHistory;