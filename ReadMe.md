# Mini Distributed Password Cracker

## Baicheng Fang, Xiaoyang Guo, Zhi Zheng

## Dependencis:

The program must run with Python3.9 (all server and worker nodes).

## To run this program:

1.  clone the repository to all machines (both server node and worker nodes). You can also run the entire program on one machine.
2.  Before you start:
    - If you want to run the program on multiple machines, make sure the "DEBUG" variable in Environment.py is 0 (**default is 0**), and the SERVER_IP is changed to the public IP of the server node.
    - If you want to run the program on a single local host, make sure the "DEBUG" variable in Environment.py is 1 (**default is 0**). You may ignore the SERVER_IP variable
3.  Open terminal on your server node, go to directory of the repository,
4.  Check dependencies of the program:

    - One machines with lower version python installed, run following command below to check if python 3.9 is installed

            pyhton3.9 --version

    - One machines without lower version python, run following command below to check if python 3.9 is installed:

             pyhton3.9 --version

5.  Start the Server process on server node with following command:

        pyhton3.9 ServerProcess.py

6.  **After the server process is running**, on each worker node, run:

        pyhton3.9 WorkerProcess.py

    Now the service is started
7. To test the basic function of the program, on any remote machine, clone the repository, go to the Environment.py, change the SERVER_IP  variable to the public IP of the server node, make sure the DEBUG variable is 0 (default is 0), go to the User.py file, modify the variable _aStr_ to any string you want to test, then run following command:
        pyhton3.9 User.py
        
The server will reply the same answer after a period of time. The time may be form 3 second over 800 second depending on number of workers and the string's property. 

Here is a video demonstrate the function:

https://user-images.githubusercontent.com/72267123/206622970-e5accbf4-d74a-4e0a-ab6b-0c59b44be4c5.mp4

