/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { Outlet, Link } from "react-router-dom";

import github from "../../assets/github.svg";
import logo from "../../assets/logo.png";

import styles from "./Layout.module.css";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link reloadDocument to="/" className={styles.headerTitleContainer}>
                        <h2 className={styles.headerTitle}>Scenario Demo</h2>
                    </Link>
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
