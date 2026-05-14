pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 45, unit: 'MINUTES')
    }

    environment {
        APP_REPO = 'https://github.com/Imranay/IdeaThoughts.git'
        TEST_REPO = 'https://github.com/Imranay/IdeaThoughts-Selenium-Tests.git'

        LOCAL_APP_URL = 'http://127.0.0.1:9090'
        PUBLIC_APP_URL = 'http://16.171.61.209/:9090'

        FALLBACK_EMAIL = 'emeebaltii007@gmail.com'
        EMAIL_RECIPIENTS = 'emeebaltii007@gmail.com'

        TEST_IMAGE = 'ideathoughts-selenium-tests'

        TRIGGER_TYPE = 'UNKNOWN'
        APP_COMMIT_AUTHOR = 'UNKNOWN'
        APP_COMMIT_EMAIL = 'UNKNOWN'
    }

    stages {

        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Detect Build Trigger') {
            steps {
                script {
                    def userCauses = currentBuild.getBuildCauses('hudson.model.Cause$UserIdCause')

                    if (userCauses != null && userCauses.size() > 0) {
                        env.TRIGGER_TYPE = 'MANUAL'
                    } else {
                        env.TRIGGER_TYPE = 'SCM_OR_WEBHOOK'
                    }

                    echo "Build Trigger Type: ${env.TRIGGER_TYPE}"
                }
            }
        }

        stage('Show Pipeline Variables') {
            steps {
                sh '''
                echo "APP_REPO=$APP_REPO"
                echo "TEST_REPO=$TEST_REPO"
                echo "LOCAL_APP_URL=$LOCAL_APP_URL"
                echo "PUBLIC_APP_URL=$PUBLIC_APP_URL"
                echo "FALLBACK_EMAIL=$FALLBACK_EMAIL"
                echo "TRIGGER_TYPE=$TRIGGER_TYPE"
                echo "TEST_IMAGE=$TEST_IMAGE"
                '''
            }
        }

        stage('Clone IdeaThoughts Application') {
            steps {
                sh '''
                echo "Cloning IdeaThoughts application repository..."
                git clone "$APP_REPO" app
                '''
            }
        }

        stage('Prepare Email Recipients') {
            steps {
                dir('app') {
                    script {
                        env.APP_COMMIT_AUTHOR = sh(
                            script: "git log -1 --pretty=%an || echo UNKNOWN",
                            returnStdout: true
                        ).trim()

                        env.APP_COMMIT_EMAIL = sh(
                            script: "git log -1 --pretty=%ae || echo UNKNOWN",
                            returnStdout: true
                        ).trim()

                        echo "App Commit Author: ${env.APP_COMMIT_AUTHOR}"
                        echo "App Commit Email: ${env.APP_COMMIT_EMAIL}"

                        def recipients = []

                        /*
                         * Manual build:
                         * Sir ko email nahi jayegi.
                         * Sirf fallback email yani aapka email use hoga.
                         */
                        if (env.TRIGGER_TYPE == 'MANUAL') {
                            recipients.add(env.FALLBACK_EMAIL)
                        }

                        /*
                         * GitHub webhook / SCM trigger:
                         * Latest app commit author ko email bhejne ki try hogi.
                         */
                        if (env.TRIGGER_TYPE == 'SCM_OR_WEBHOOK') {
                            recipients.add(env.FALLBACK_EMAIL)

                            def email = env.APP_COMMIT_EMAIL?.trim()

                            if (
                                email &&
                                email.toLowerCase() != 'null' &&
                                email.toLowerCase() != 'unknown' &&
                                email.toLowerCase() != 'admin' &&
                                email.contains('@') &&
                                !email.toLowerCase().contains('noreply')
                            ) {
                                recipients.add(email)
                            }
                        }

                        env.EMAIL_RECIPIENTS = recipients
                            .findAll { it && it.contains('@') && it.toLowerCase() != 'null' }
                            .unique()
                            .join(',')

                        echo "Final Email Recipients: ${env.EMAIL_RECIPIENTS}"
                    }
                }
            }
        }

        stage('Start IdeaThoughts Application') {
            steps {
                dir('app') {
                    sh '''
                    echo "Removing old containers if they exist..."
                    docker rm -f ideathoughts_app ideathoughts_db || true

                    echo "Stopping old Docker Compose environment..."
                    docker compose down -v --remove-orphans || true

                    echo "Starting IdeaThoughts application with Docker Compose..."
                    docker compose up -d --build

                    echo "Waiting for MySQL and Flask application to become ready..."
                    sleep 60

                    echo "Currently running containers:"
                    docker ps
                    '''
                }
            }
        }

        stage('Check Application Reachability') {
            steps {
                sh '''
                echo "Checking application reachability at $LOCAL_APP_URL"

                for i in $(seq 1 30); do
                    if curl -fsS "$LOCAL_APP_URL" > /dev/null; then
                        echo "Application is reachable."
                        exit 0
                    fi

                    echo "Application not ready yet. Attempt $i/30"
                    sleep 5
                done

                echo "Application failed to become reachable."

                echo "IdeaThoughts app logs:"
                docker logs ideathoughts_app || true

                echo "IdeaThoughts database logs:"
                docker logs ideathoughts_db || true

                exit 1
                '''
            }
        }

        stage('Clone Selenium Test Code') {
            steps {
                sh '''
                echo "Cloning Selenium test repository..."
                git clone "$TEST_REPO" tests
                '''
            }
        }

        stage('Build Selenium Test Image') {
            steps {
                dir('tests') {
                    sh '''
                    echo "Building Selenium test Docker image..."
                    docker build -t "$TEST_IMAGE" .
                    '''
                }
            }
        }

        stage('Run Selenium Tests in Docker') {
            steps {
                dir('tests') {
                    sh '''
                    echo "Creating reports folder..."
                    mkdir -p reports

                    echo "Running Selenium tests against $LOCAL_APP_URL"

                    docker run --rm \
                      --network host \
                      -e APP_URL="$LOCAL_APP_URL" \
                      -v "$PWD/reports:/tests/reports" \
                      "$TEST_IMAGE"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Archiving Selenium test reports..."

            archiveArtifacts artifacts: 'tests/reports/*', allowEmptyArchive: true
            junit testResults: 'tests/reports/results.xml', allowEmptyResults: true

            echo "Sending Jenkins email notification to: ${env.EMAIL_RECIPIENTS}"

            mail(
                to: "${env.EMAIL_RECIPIENTS}",
                subject: "IdeaThoughts Jenkins Test Result: ${currentBuild.currentResult} | Build #${env.BUILD_NUMBER}",
                body: """
Project: IdeaThoughts

Build Status:
${currentBuild.currentResult}

Build Number:
${env.BUILD_NUMBER}

Build Trigger Type:
${env.TRIGGER_TYPE}

Application Commit Author:
${env.APP_COMMIT_AUTHOR}

Application Commit Email:
${env.APP_COMMIT_EMAIL}

Public Application URL:
${env.PUBLIC_APP_URL}

Local Application URL Used for Selenium:
${env.LOCAL_APP_URL}

Jenkins Build URL:
${env.BUILD_URL}

Selenium test results are available inside Jenkins build artifacts.

This email was sent automatically by Jenkins after running the Dockerized Selenium test pipeline.
"""
            )
        }

        cleanup {
            echo "Cleaning Docker containers and test image..."

            dir('app') {
                sh '''
                docker compose down -v --remove-orphans || true
                docker rm -f ideathoughts_app ideathoughts_db || true
                '''
            }

            sh '''
            docker rmi "$TEST_IMAGE" || true
            docker system prune -f || true
            '''
        }
    }
}
