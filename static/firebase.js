// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
} from "firebase/auth";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBGaOslBXh3QQ7-JcJeIW14fQMkm6qWfdI",
  authDomain: "employee-dashboard-3d504.firebaseapp.com",
  projectId: "employee-dashboard-3d504",
  storageBucket: "employee-dashboard-3d504.appspot.com",
  messagingSenderId: "1997859987",
  appId: "1:1997859987:web:d176bec602c61b14003166",
  measurementId: "G-NK9ZBKNZXP",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const googleProvider = new GoogleAuthProvider();

const signInWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    // Handle user information and role assignment
  } catch (error) {
    console.error("Error during sign-in:", error);
  }
};

const logOut = async () => {
  try {
    await signOut(auth);
  } catch (error) {
    console.error("Error during sign-out:", error);
  }
};

export { auth, db, signInWithGoogle, logOut };
