**0. Get sources**

    git clone https://github.com/0xVK/DiplomaCreator.git

**1. Go to folder**

    cd DiplomaCreator

**2.Create virtual environment**

    python3 -m venv venv

**3. Activate virtual environment**

    source venv/bin/activate

**4. Install requirements**

    pip3 install -r requirements.txt

**5. To run site use:**

    python3 main.py
---
   **Set site to autorun:**

    sudo cp diploma-creator.service /etc/systemd/system/
    systemctl start diploma-creator.service
    systemctl enable diploma-creator.service

**Check status**

    systemctl status diploma-creator.service

**Open in browser**

    http://0.0.0.0:8080/




