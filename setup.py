from distutils.core import setup


def read_requirements(requirements_file="requirements.in"):
    with open(requirements_file) as f:
        return [requirement.strip() for requirement in f.readlines()]


setup(
    name="thumbling",
    description="Check Prometheus for alerts from chat",
    author="Bjoern Meier",
    author_email="bjoern.meier@jda.com",
    packages=["thumbling"],
    package_dir={"": "src"},
    install_requires=read_requirements(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
