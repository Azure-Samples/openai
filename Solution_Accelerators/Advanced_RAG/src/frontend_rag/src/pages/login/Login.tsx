/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Modal from "react-modal";
import { Styles } from "react-modal";
import { useMsal } from "@azure/msal-react";

import styles from "./Login.module.css";

export const ModalStyle: Styles = {
    content: {
        position: "relative",
        width: "500px",
        margin: "50px auto",
        border: "1px solid #ccc",
        filter: "blur(0)",
        opacity: 1,
        visibility: "visible",
        boxShadow: "-2rem 2rem 2rem rgba(0, 0, 0, 0.5)",
        outline: 0,
        fontSize: "1.1em",
        fontWeight: "bold",
        backgroundColor: "#FFFFFF",
        overflow: "hidden"
    },
    overlay: {
        backgroundColor: "rgba(255, 255, 255, 0.6)"
    }
};

const Login = () => {
    const [isOpen, setIsOpen] = useState(true);

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [emailError, setEmailError] = useState("");
    const [passwordError, setPasswordError] = useState("");

    const toggleModal = () => {
        setIsOpen(!isOpen);
    };

    let navigate = useNavigate();
    const navigateToChat = () => {
        let path = `chat`;
        navigate(path);
    };

    const { instance, accounts } = useMsal();

    const loginRequest = {
        scopes: ["User.Read"]
    };

    const handleLogin = () => {
        instance.loginRedirect(loginRequest).catch(e => {
            console.log(e);
        });
    };

    return (
        <div className={styles.mainContainer}>
            {/* <button className={styles.buttonContainer} onClick={toggleModal}>
                Login
            </button> */}
            <Modal style={ModalStyle} isOpen={isOpen} onRequestClose={toggleModal} shouldCloseOnOverlayClick={false} shouldCloseOnEsc={false}>
                <div className={styles.titleContainer}>Login</div>
                <div className={styles.inputContainer}>
                    <input className={styles.buttonContainer} type="button" onClick={handleLogin} value={"Sign in"} />
                </div>
            </Modal>
        </div>
    );
};

export default Login;
