pipeline {
    agent any

    environment {
        APP_REPO = 'https://github.com/Imranay/IdeaThoughts.git'
        TEST_REPO = 'https://github.com/Imranay/IdeaThoughts-Selenium-Tests.git'
        APP_URL = 'http://127.0.0.1:9090'
        PUBLIC_APP_URL = 'http://16.16.127.48:9090'
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Clone IdeaThoughts Application') {
            steps {
                sh 'git clone $APP_REPO app'
            }
        }

        stage('Start IdeaThoughts Application') {
            steps {
                dir('app') {
                    sh 'docker compose down || true'
                    sh 'docker compose up -d --build'
                    sh 'sleep 60'
                    sh 'docker ps'
                }
            }
        }

        stage('Check Application Reachability') {
            steps {
                sh 'curl -I $APP_URL || exit 1'
            }
        }

        stage('Clone Selenium Test Code') {
            steps {
                sh 'git clone $TEST_REPO tests'
            }
        }

        stage('Build Selenium Test Image') {
            steps {
                dir('tests') {
                    sh 'docker build -t ideathoughts-selenium-tests .'
                }
            }
        }

        stage('Run Selenium Tests in Docker') {
            steps {
                dir('tests') {
                    sh '''
                    mkdir -p reports

                    docker run --rm \
                      --network host \
                      -e APP_URL=$APP_URL \
                      -v "$PWD/reports:/tests/reports" \
                      ideathoughts-selenium-tests
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'tests/reports/*', allowEmptyArchive: true
            junit 'tests/reports/results.xml'

            emailext(
                subject: "IdeaThoughts Jenkins Test Result: ${currentBuild.currentResult}",
                body: """
                Project: IdeaThoughts

                Build Status: ${currentBuild.currentResult}

                Public Application URL:
                ${PUBLIC_APP_URL}

                Jenkins Build URL:
                ${env.BUILD_URL}

                Selenium test report is attached/archived in Jenkins build artifacts.
                """,
                to: 'qasimalik@gmail.com, emeebaltii007@gmail.com'
            )
        }

        cleanup {
            dir('app') {
                sh 'docker compose down || true'
            }
        }
    }
}