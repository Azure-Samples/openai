# Fully utilize AOAI quotas and limits
As of 12 June 2023, one subscription can provision 30 AOAI resources per region, sharing the same TPM and RPM limits. For example, you can allocate 3 deployment instances of GPT-35-Turbo with 80K TPM/480 RPM each to utilize the whole TPM/RPM limits for one region.
Currently, there are four regional Cognitive services that support Azure OpenAI -EastUS, South Cental US, West Europe and France Central which allows for a maximium 120 instances of the same AOAI model can be provisoned across these four regions. This means you can achieve up to (1440x4/60) = maximium 96 request per second for your ChatGPT model. If this is still not enough to meet your production workload requirements, you can consider getting additional subscriptions to create an AOAI resources RAID.

[Read More](https://github.com/denlai-mshk/aoai-fwdproxy-funcapp)
