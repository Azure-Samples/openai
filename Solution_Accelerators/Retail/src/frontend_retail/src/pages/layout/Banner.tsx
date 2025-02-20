import styles from "./Banner.module.css";

const Banner = () => {
    return (
        <div>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <div className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>Contoso Shopping Assistant</h3>
                    </div>
                </div>
            </header>
        </div>
    );
};

export default Banner;
