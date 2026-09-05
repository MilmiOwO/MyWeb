const loginMessages=[
    "Verifying it's you",
    "Is it you, Milmi?",
    "Good to see you again."
];

const message=loginMessages[Math.floor(Math.random()*loginMessages.length)];
document.getElementById("login-form__title").textContent=message