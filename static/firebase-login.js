'use strict';

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";

// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyC7GYHoIZjG02prIDGfYBLQDI1o9OAYDFc",
  authDomain: "room-booking-38d16.firebaseapp.com",
  projectId: "room-booking-38d16",
  storageBucket: "room-booking-38d16.appspot.com",
  messagingSenderId: "472075646045",
  appId: "1:472075646045:web:f3aac2e3d6232bea8d09b4",
  measurementId: "G-XCZML03C1Y"
};


console.log("Script loaded");

window.addEventListener("load", function () {

  const app = initializeApp(firebaseConfig);

  const auth = getAuth(app);

  updateUI(document.cookie);

  console.log("hello world load");

  document.getElementById("sign-up").addEventListener('click', function () {
    // signup of a new user to firebase document.getElementById("sign-up").addEventListener('click', function() {

    const email = document.getElementById("email").value

    const password = document.getElementById("password").value

    createUserWithEmailAndPassword(auth, email, password)

      .then((userCredential) => {

        // we have a created user

        const user = userCredential.user;

        // get the id token for the user who just logged in and force a redirect to

        user.getIdToken().then((token) => {

          document.cookie = "token=" + token + ";path=/;SameSite=Strict";

          window.location = "/static/booking.html";
s
        });

      })

      .catch((errог) => {

        // issue with signup that we will drop to console console.log(error.code + error.message);
        console.log(errог.code + errог.message);

      })

  });


  // login of a user to firebase

  document.getElementById("login").addEventListener('click', function () {

    const email = document.getElementById("email").value

    const password = document.getElementById("password").value

    signInWithEmailAndPassword(auth, email, password)

      .then((userCredential) => {

        const user = userCredential.user;

        console.log("logged in");

        // get the id token for the user who just logged in and force a redirect to /

        user.getIdToken().then((token) => {

          document.cookie = "token=" + token + ";path=/;SameSite=Strict";
          window.location = "/static/booking.html";
        });

      })
      .catch((error) => {

        // issue with signup that we will drop to console console.log(error.code error.message);
        console.log(error.code + error.message);

      })

  });



  // document.getElementById("sign-out").addEventListener('click', function () {
  //   signOut(auth)
  //     .then((output) => {
  //       document.cookie = "token=;path=/;SameSite=Strict";
  //       window.location = "/";
  //     })
  // });


});


function updateUI(cookie) {
  var token = parseCookieToken(cookie);
  if (token.length > 0) {
    document.getElementById("login-box").hidden = true;
    // document.getElementById("sign-out").hidden = false;
  } else {
    document.getElementById("login-box").hidden = false;
    // document.getElementById("sign-out").hidden = true; // Corrected typo
  }
}


function parseCookieToken(cookie) {

  // split the cookie out on the basis of the semi colon

  var strings = cookie.split(';');

  // go through each of the strings

  for (let i = 0; i < strings.length; i++) {

    // split the string based on the = sign. if the LHS is token

    var temp = strings[i].split('=');

    if (temp[0] == "token")

      return temp[1];

  }



  // if we got to this point then token wasn't in the cookie so retu return "";

  return "";

};
