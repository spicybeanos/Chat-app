const express = require('express')
const fs = require('node:fs');
const bodyParser = require('body-parser');
const path = require('path');
const session = require('express-session');
const { send } = require('node:process');


const app = express();
const port = 3000;

app.use(session({
    secret: 'your-secret-key', // Replace with a strong secret
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false } // Set to true if using HTTPS
}));

const filePaths = {
    form: path.join(__dirname, 'static/form.temp.html'),
    home: path.join(__dirname, 'static/home.temp.html'),
    c_me: path.join(__dirname, 'static/chat.me.html'),
    c_other: path.join(__dirname, 'static/chat.other.html'),
    chatSend: path.join(__dirname, 'static/chat.send.html'),
    login: path.join(__dirname, 'static/login.temp.html'),
    register: path.join(__dirname, 'static/register.temp.html')
}
const endpoints = {
    authentication: "http://127.0.0.1:6060",
    authentication_login: "http://127.0.0.1:6060/login",
    authentication_register: "http://127.0.0.1:6060/register",
    send_message: "http://127.0.0.1:6070",
    chat: "http://127.0.0.1:6080",
}
const api_keys = {
    chat: "abcd1234",
    addMsg: "add_msgs_key_123409876",
    authentication: "your_secure_api_key"
}

function make404(message) {
    return `<h1 style='font-family:sans-serif'>404 Not found</h1>\n<p style='font-family:sans-serif'>${message}</p>`
}
function makeTitleMsg(title, msg) {
    return `<h1 style='font-family:sans-serif'>${title}</h1>\n<p style='font-family:sans-serif'>${msg}</p>`
}

const _login = (fs.readFileSync(filePaths.login)).toString();
const _reg = (fs.readFileSync(filePaths.register)).toString();
const _home = (fs.readFileSync(filePaths.home)).toString();
const _chatForm = (fs.readFileSync(filePaths.form)).toString();
function renderLoginPage() {
    return (_home.toString()).replace('{CONT}', _login);
}
function renderRegisterPage() {
    return (_home.toString()).replace('{CONT}', _reg);
}

function renderHomePage(user) {
    return (_home.toString()).replace('{CONT}', _chatForm).replace('{USER}',user);
}

const t_me = (fs.readFileSync(filePaths.c_me)).toString();
const t_other = (fs.readFileSync(filePaths.c_other)).toString();
function renderOneChat(sender, content, is_sender) {
    if (is_sender) {
        return (t_me.replace("{NAME}", sender)).replace("{CONTENT}", content) + "\n";
    } else {
        return (t_other.replace("{NAME}", sender)).replace("{CONTENT}", content) + "\n";
    }
}

app.use(express.static('static'))
app.use(bodyParser.urlencoded({ extended: true }));

function checkAuth(req, res, next) {
    if (req.session.user) {
        next(); // Proceed if the user is logged in
    } else {
        res.redirect('/login'); // Redirect to login if not logged in
    }
}

async function validateUser(user, pass) {
    try {
        const res = await fetch(endpoints.authentication_login, {
            method: "POST",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: api_keys.authentication,
                username: user,
                password: pass
            })
        });
        if (res.status === 200) return true;
        else return false;
    } catch (exc) {
        console.log("Could not validate:\n" + exc);
        return false;
    }
}

app.post('/login', (req, res) => {
    const { username, password } = req.body;
    // Validate username and password with the database
    if (validateUser(username, password)) {
        req.session.user = { username }; // Store user info in the session
        res.redirect('/');
    } else {
        res.status(401).send('Invalid credentials');
    }
});

app.post('/register', (req, res) => {
    const { username, password } = req.body;
    fetch(endpoints.authentication_register, {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            api_key: api_keys.authentication,
            username: username,
            password: password
        })
    }).then((resp_reg) => {

        if (resp_reg.status === 403) {
            res.send("invalid api key");
            res.redirect('/login');
        }
        if (resp_reg.status === 400) {
            res.send("username and password required");
            res.redirect('/login');
        }
        if (resp_reg.status === 409) {
            res.send("username already exists");
            res.redirect('/login');
        }
        if (resp_reg.status === 201) {
            req.session.user = { username };
            res.redirect('/');
        }
        else {
            res.send("got this error")
        }

    })


});

app.get('/', checkAuth, (req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.write(renderHomePage(req.session.user.username));
    return res.end();
});

app.get('/login', (req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.write(renderLoginPage());
    return res.end();
});
app.get('/register', (req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.write(renderRegisterPage());
    return res.end();
});

app.post('/chat', checkAuth, (req, res) => {
    const message = req.body.msg;
    const sender = req.session.user.username;
    const recv = req.query.username;
    fetch(endpoints.send_message + '/add_message', {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: sender,
            receiver: recv,
            message: message,
            api_key: api_keys.addMsg
        })
    }).then((r) => {
        if (r.status === 200 || r.status === 201) {


            const me = sender;
            const username = recv;
            fetch(
                endpoints.chat +
                `/get_messages?me=${sender}&receiver=${recv}&api_key=${api_keys.chat}`, {
                method: "GET" // default, so we can ignore
            }).then((gc_res) => {
                gc_res.json().then((val) => {

                    //read the template, replace the placeholders
                    // then do for each of the messages
                    // then inject into homepage html
                    //send the html to client
                    const t_send = (fs.readFileSync(filePaths.chatSend)).toString()
                    const t_me = (fs.readFileSync(filePaths.c_me)).toString();
                    const t_other = (fs.readFileSync(filePaths.c_other)).toString();
                    let chats = `<p>${me}  & ` + username + `</p>\n${t_send}\n`;

                    val.forEach(ms => {
                        if (ms.receiver === me) {
                            chats = chats.concat(t_other.replace("{NAME}", recv).replace("{CONTENT}", ms.content)) + "\n";
                        } else {
                            chats = chats.concat(t_me.replace("{NAME}", sender).replace("{CONTENT}", ms.content)) + "\n";
                        }
                    });

                    const hm = fs.readFileSync(filePaths.home).toString();

                    res.writeHead(200, { 'Content-Type': 'text/html' });
                    res.write(hm.replace('{CONT}', chats));
                    return res.end();


                }).catch((exc) => {
                    console.log("Error!\n" + exc)
                    res.writeHead(500, { 'Content-Type': 'text/html' })
                    res.write(exc);
                    return res.end()
                });
            }).catch((exc) => {
                console.log("Error!\n" + exc)
                res.writeHead(500, { 'Content-Type': 'text/html' })
                res.write(exc);
                return res.end()
            });


        }
        else {
            res.writeHead(500, { 'Content-Type': 'text/html' });
            res.write(makeTitleMsg(":(", "Something went wrong...\n" + r.status + ":" + r.statusText))
            return res.end();
        }
    }).catch((exc) => {
        console.error(exc);
        res.writeHead(500, { 'Content-Type': 'text/html' });
        res.write(makeTitleMsg(":(", "Something went wrong...\n" + exc));
        res.end();
    });
});

app.get('/chat', checkAuth, (req, res) => {
    if (req.query.username) {
        const username = req.query.username;
        const me = req.session.user.username;
        if (username === '' || me === '') {
            res.send('empty field(s)!');
            console.log("Empty query fields!");
            return res.end();
        }

        fetch(
            endpoints.chat +
            `/get_messages?me=${me}&receiver=${username}&api_key=${api_keys.chat}`, {
            method: "GET" // default, so we can ignore
        }).then((gc_res) => {
            gc_res.json().then((val) => {

                //read the template, replace the placeholders
                // then do for each of the messages
                // then inject into homepage html
                //send the html to client
                const t_send = (fs.readFileSync(filePaths.chatSend)).toString()
                let chats = `<p>Logged in as ${req.session.user.username}</p>\n<p>${me}  & ` + username + `</p>\n${t_send}\n`;

                val.forEach(ms => {
                    chats = chats.concat(renderOneChat(ms.sender, ms.content, ms.sender === me));
                });

                res.writeHead(200, { 'Content-Type': 'text/html' });
                res.write(_home.replace('{CONT}', chats));
                return res.end();


            }).catch((exc) => {
                console.log("Error!\n" + exc)
                res.writeHead(500, { 'Content-Type': 'text/html' })
                res.write(exc);
                return res.end()
            });
        }).catch((exc) => {
            console.log("Error!\n" + exc)
            res.writeHead(500, { 'Content-Type': 'text/html' })
            res.write(exc);
            return res.end()
        });
    } else {
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.write(make404('No username field :(!'));
        return res.end();
    }
});

app.listen(port, () => {
    console.log(`Example app listening on port ${port}`)
    console.log(`url : http://127.0.0.1:${port}`)
})