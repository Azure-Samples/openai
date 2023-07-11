import { Outlet, Link } from "react-router-dom";

import github from "../../assets/github.svg";

import styles from "./Layout.module.css";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link reloadDocument to="/" className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>GPT + Enterprise data | Sample</h3>
                    </Link>
                    <nav>
                        <ul className={styles.headerNavList}>
                            <li className={styles.headerNavLeftMargin}>
                                {/** TODO: update github link below once new repo is setup.*/}
                                <a
                                    className={styles.githubLink}
                                    href="https://github.com/Azure-Samples/openai/tree/main/End_to_end_Solutions/AOAISearchDemo"
                                    target={"_blank"}
                                    title="Github repository link"
                                >
                                    <img
                                        src={github}
                                        alt="Github logo"
                                        aria-label="Link to github repository"
                                        width="20px"
                                        height="20px"
                                        className={styles.githubLogo}
                                    />
                                    <span className={styles.githubText}>Source Code</span>
                                </a>
                            </li>
                        </ul>
                    </nav>
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
