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
        PUBLIC_APP_URL = 'http://16.16.127.48:9090'

        EMAIL_RECIPIENTS = 'qasimalik@gmail.com,emeebaltii007@gmail.com'
        TEST_IMAGE = 'ideathoughts-selenium-tests'
    }

    stages {

        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Show Pipeline Variables') {
            steps {
                sh '''
                echo "APP_REPO=$APP_REPO"
                echo "TEST_REPO=$TEST_REPO"
                echo "LOCAL_APP_URL=$LOCAL_APP_URL"
                echo "PUBLIC_APP_URL=$PUBLIC_APP_URL"
                echo "EMAIL_RECIPIENTS=$EMAIL_RECIPIENTS"
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

            echo "Sending Jenkins email notification..."

            mail(
                to: "${env.EMAIL_RECIPIENTS}",
                subject: "IdeaThoughts Jenkins Test Result: ${currentBuild.currentResult} | Build #${env.BUILD_NUMBER}",
                body: """
Project: IdeaThoughts

Build Status:
${currentBuild.currentResult}

Build Number:
${env.BUILD_NUMBER}

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